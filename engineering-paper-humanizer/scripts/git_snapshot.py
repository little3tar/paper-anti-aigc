#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engineering-paper-humanizer 智能备份脚本

智能备份策略（按优先级）：
1. Git 分支备份（首选）- 若当前目录是 Git 仓库或可以初始化为 Git 仓库
2. 文件复制备份（回退）- 若 Git 不可用或未安装

支持功能：
- 自动 Git 初始化：非 Git 目录自动执行 git init
- 智能回退：Git 命令不可用时自动切换到文件复制备份
- 完整备份生命周期：创建、列出、回滚、对比、清理

用法:
python3 scripts/git_snapshot.py main.tex              # 创建备份
python3 scripts/git_snapshot.py --list               # 列出所有备份
python3 scripts/git_snapshot.py --rollback           # 从最近备份恢复
python3 scripts/git_snapshot.py --rollback <branch>  # 从指定备份恢复
python3 scripts/git_snapshot.py --diff main.tex      # 对比差异
python3 scripts/git_snapshot.py --cleanup            # 清理旧备份（需确认）
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import sys
import io
import os

# Windows GBK 终端兼容：强制 UTF-8 输出
if os.name == "nt":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


BACKUP_PREFIX = "backup/humanizer/"
MAX_BACKUPS = 5  # 保留的最大备份数量
FILE_BACKUP_DIR = ".humanizer-backups"  # 文件复制备份目录


# ── 工具函数 ───────────────────────────────────────────────


def run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """执行 git 命令并返回结果"""
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", check=check
    )


def is_git_available() -> bool:
    """检测系统是否安装了 Git"""
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, encoding="utf-8"
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def is_git_repo() -> bool:
    """检测当前目录是否处于 Git 仓库内"""
    result = run_git("rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def try_git_init() -> bool:
    """尝试初始化 Git 仓库，返回是否成功"""
    result = run_git("init")
    if result.returncode != 0:
        print(f"[WARN] Git 初始化失败：{result.stderr.strip()}")
        return False
    print("[INFO] Git 仓库已自动初始化")
    return True


def get_backup_branches() -> list[str]:
    """获取所有备份分支名，按时间倒序（最新在前）"""
    result = run_git(
        "branch", "--list", f"{BACKUP_PREFIX}*", "--format=%(refname:short)"
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    branches = result.stdout.strip().split("\n")
    branches.sort(reverse=True)  # 分支名含时间戳，字典序倒排即时间倒序
    return branches


def ensure_git_ready() -> dict:
    """确保 Git 环境就绪，返回状态字典

    返回: {
        "available": bool,  # Git 是否可用
        "is_repo": bool,    # 是否是 Git 仓库
        "ready": bool,      # 是否可以进行 Git 备份
        "mode": str         # "git" | "file"
    }
    """
    status = {
        "available": is_git_available(),
        "is_repo": is_git_repo(),
        "ready": False,
        "mode": "file"
    }

    if not status["available"]:
        print("[INFO] Git 未安装或不可用，将使用文件复制备份")
        return status

    if status["is_repo"]:
        status["ready"] = True
        status["mode"] = "git"
        return status

    # 尝试初始化 Git
    print("[INFO] 当前目录不是 Git 仓库，尝试自动初始化...")
    if try_git_init():
        status["is_repo"] = True
        status["ready"] = True
        status["mode"] = "git"
    else:
        print("[INFO] Git 初始化失败，将使用文件复制备份")

    return status


def get_file_backup_dir() -> Path:
    """获取文件备份目录路径（在仓库根目录下）"""
    # 尝试获取仓库根目录，如果失败则使用当前工作目录
    if is_git_repo():
        result = run_git("rev-parse", "--show-toplevel")
        if result.returncode == 0:
            repo_root = Path(result.stdout.strip())
            return repo_root / FILE_BACKUP_DIR
    # 回退到当前目录
    return Path.cwd() / FILE_BACKUP_DIR


def get_file_backups(filepath: str) -> list[Path]:
    """获取指定文件的所有文件备份，按时间倒序（最新在前）"""
    backup_dir = get_file_backup_dir()
    if not backup_dir.exists():
        return []

    path = Path(filepath)
    pattern = f"{path.stem}_*.{path.suffix.lstrip('.')}" if path.suffix else f"{path.stem}_*"
    backups = sorted(backup_dir.glob(pattern), reverse=True)
    return backups


# ── Git 备份功能 ───────────────────────────────────────────────


def git_backup(filepath: str, dry_run: bool = False) -> bool:
    """使用 Git 分支备份文件

    参数:
        filepath: 要备份的文件路径
        dry_run: 模拟模式

    返回:
        备份是否成功
    """
    if dry_run:
        print(f"[DRY-RUN] 模拟 Git 备份: {filepath}")
        print(f"[DRY-RUN] 实际将执行以下操作：")
        print(f"  1. 检查 Git 仓库状态")
        print(f"  2. 对比文件与最近备份的差异（如果有）")
        print(f"  3. 创建备份分支")
        print(f"  4. 自动淘汰超出 {MAX_BACKUPS} 个限制的旧备份")
        return True

    if not is_git_repo():
        print("[WARN] Git 仓库不可用，无法创建分支备份")
        return False

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过分支备份")
        return False

    # 检测是否有提交 - 空仓库无法创建分支
    head_check = run_git("rev-parse", "--verify", "HEAD")
    if head_check.returncode != 0:
        print("[WARN] 仓库尚无任何提交（空仓库），请先执行 git commit 后再使用 Git 备份功能")
        print("[INFO] 将尝试文件复制备份作为替代...")
        return False

    # 获取文件相对于仓库根目录的路径
    repo_root_result = run_git("rev-parse", "--show-toplevel")
    if repo_root_result.returncode != 0:
        print("[WARN] 无法获取仓库根目录")
        return False
    repo_root = Path(repo_root_result.stdout.strip())

    try:
        rel_path = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        print(f"[WARN] 文件 {filepath} 不在仓库内")
        return False

    # 跳过空提交：对比文件内容与最近备份
    branches = get_backup_branches()
    if branches:
        latest = branches[0]
        old_hash_result = run_git("rev-parse", f"{latest}:{rel_path}")
        if old_hash_result.returncode == 0:
            old_hash = old_hash_result.stdout.strip()
            new_hash_result = run_git("hash-object", str(path))
            if new_hash_result.returncode == 0:
                new_hash = new_hash_result.stdout.strip()
                if old_hash == new_hash:
                    print(f"[INFO] {filepath} 与最近 Git 备份内容相同，跳过备份")
                    return True

    # 创建备份分支
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_branch = f"{BACKUP_PREFIX}{timestamp}"

    # Step 1: 将文件写入 git 对象库
    blob_result = run_git("hash-object", "-w", str(path))
    if blob_result.returncode != 0:
        print(f"[WARN] hash-object 失败：{blob_result.stderr.strip()}")
        return False
    blob_hash = blob_result.stdout.strip()

    # Step 2: 基于当前 HEAD 的 tree 构建新 tree
    head_tree_result = run_git("rev-parse", "HEAD^{tree}")
    if head_tree_result.returncode != 0:
        print(f"[WARN] 无法读取 HEAD tree：{head_tree_result.stderr.strip()}")
        return False
    head_tree = head_tree_result.stdout.strip()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".idx") as tmp:
        tmp_index = tmp.name

    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = tmp_index

    try:
        # 读取 HEAD tree 到临时 index
        r = subprocess.run(
            ["git", "read-tree", head_tree],
            capture_output=True, text=True, encoding="utf-8", env=env
        )
        if r.returncode != 0:
            print(f"[WARN] read-tree 失败：{r.stderr.strip()}")
            return False

        # 在临时 index 中更新目标文件
        r = subprocess.run(
            ["git", "update-index", "--add", "--cacheinfo",
             f"100644,{blob_hash},{rel_path}"],
            capture_output=True, text=True, encoding="utf-8", env=env
        )
        if r.returncode != 0:
            print(f"[WARN] update-index 失败：{r.stderr.strip()}")
            return False

        # 写出新 tree
        r = subprocess.run(
            ["git", "write-tree"],
            capture_output=True, text=True, encoding="utf-8", env=env
        )
        if r.returncode != 0:
            print(f"[WARN] write-tree 失败：{r.stderr.strip()}")
            return False
        new_tree = r.stdout.strip()
    finally:
        try:
            os.unlink(tmp_index)
        except OSError:
            pass

    # Step 3: 创建 commit 对象
    head_result = run_git("rev-parse", "HEAD")
    if head_result.returncode != 0:
        print(f"[WARN] 无法获取 HEAD：{head_result.stderr.strip()}")
        return False
    head_sha = head_result.stdout.strip()

    commit_msg = f"[humanizer-backup] {path.name} @ {timestamp}"
    commit_result = run_git("commit-tree", new_tree, "-p", head_sha, "-m", commit_msg)
    if commit_result.returncode != 0:
        print(f"[WARN] commit-tree 失败：{commit_result.stderr.strip()}")
        return False
    commit_sha = commit_result.stdout.strip()

    # Step 4: 创建备份分支
    ref_result = run_git("update-ref", f"refs/heads/{backup_branch}", commit_sha)
    if ref_result.returncode != 0:
        print(f"[WARN] 创建备份分支失败：{ref_result.stderr.strip()}")
        return False

    print(f"[OK] 已创建 Git 备份分支：{backup_branch}")

    # 自动淘汰旧备份
    _auto_evict_old_backups()
    return True


def _auto_evict_old_backups() -> None:
    """当备份分支数超过 MAX_BACKUPS 时，自动删除最旧的备份"""
    branches = get_backup_branches()
    if len(branches) <= MAX_BACKUPS:
        return

    to_delete = branches[MAX_BACKUPS:]  # 超出部分（最旧的）
    for b in to_delete:
        result = run_git("branch", "-D", b)
        if result.returncode == 0:
            print(f"[INFO] 自动淘汰旧 Git 备份：{b}")


# ── 文件复制备份功能 ─────────────────────────────────────────


def file_backup(filepath: str, dry_run: bool = False) -> bool:
    """使用文件复制备份文件

    参数:
        filepath: 要备份的文件路径
        dry_run: 模拟模式

    返回:
        备份是否成功
    """
    if dry_run:
        print(f"[DRY-RUN] 模拟文件备份: {filepath}")
        print(f"[DRY-RUN] 实际将执行以下操作：")
        print(f"  1. 创建备份目录: {FILE_BACKUP_DIR}")
        print(f"  2. 复制文件并添加时间戳")
        print(f"  3. 自动淘汰超出 {MAX_BACKUPS} 个限制的旧备份")
        return True

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过备份")
        return False

    # 确保备份目录存在
    backup_dir = get_file_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 检查是否与最近备份相同（使用内容哈希）
    recent_backups = get_file_backups(filepath)
    if recent_backups:
        latest_backup = recent_backups[0]
        current_hash = hashlib.md5(path.read_bytes()).hexdigest()
        backup_hash = hashlib.md5(latest_backup.read_bytes()).hexdigest()
        if current_hash == backup_hash:
            print(f"[INFO] {filepath} 与最近文件备份内容相同，跳过备份")
            return True

    # 创建带时间戳的备份文件名
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{path.stem}_{timestamp}{path.suffix}"
    backup_path = backup_dir / filename

    try:
        shutil.copy2(path, backup_path)
        print(f"[OK] 已创建文件备份: {backup_path.relative_to(Path.cwd())}")
    except Exception as e:
        print(f"[WARN] 文件备份失败: {e}")
        return False

    # 自动淘汰旧备份
    _auto_evict_file_backups(filepath)
    return True


def _auto_evict_file_backups(filepath: str) -> None:
    """删除超出限制的旧文件备份"""
    backups = get_file_backups(filepath)
    if len(backups) <= MAX_BACKUPS:
        return

    to_delete = backups[MAX_BACKUPS:]
    for backup in to_delete:
        try:
            backup.unlink()
            print(f"[INFO] 自动淘汰旧文件备份: {backup.name}")
        except OSError as e:
            print(f"[WARN] 删除旧备份失败 {backup.name}: {e}")


# ── 统一的备份入口 ───────────────────────────────────────────


def cmd_snapshot(filepath: str, dry_run: bool = False) -> None:
    """智能备份入口 - 自动选择 Git 或文件备份"""
    if dry_run:
        print(f"[DRY-RUN] 模拟备份文件: {filepath}")
        print("=" * 50)

    # 检测并准备备份环境
    status = ensure_git_ready()

    # 首选 Git 备份
    if status["mode"] == "git" and status["ready"]:
        if git_backup(filepath, dry_run):
            return
        print("[INFO] Git 备份失败，尝试文件备份...")

    # 回退到文件备份
    file_backup(filepath, dry_run)


# ── 其他命令功能 ─────────────────────────────────────────────


def cmd_list() -> None:
    """列出所有备份（Git 分支 + 文件复制）"""
    print("=" * 50)
    print("备份列表")
    print("=" * 50)

    # 列出 Git 备份
    if is_git_repo():
        branches = get_backup_branches()
        if branches:
            print(f"\n[Git 分支备份] 共 {len(branches)} 个（最新在前）：")
            for branch in branches:
                log_result = run_git("log", branch, "-1", "--format=%ai %s")
                info = log_result.stdout.strip() if log_result.returncode == 0 else ""
                print(f"  {branch}")
                if info:
                    print(f"    └─ {info}")
        else:
            print("\n[Git 分支备份] 暂无")
    else:
        print("\n[Git 分支备份] Git 仓库不可用")

    # 列出文件备份
    backup_dir = get_file_backup_dir()
    if backup_dir.exists():
        all_backups = sorted(backup_dir.iterdir(), reverse=True)
        backups = [f for f in all_backups if f.is_file()]
        if backups:
            print(f"\n[文件复制备份] 目录: {FILE_BACKUP_DIR}/")
            print(f"               共 {len(backups)} 个（最新在前）：")
            for backup in backups[:10]:  # 最多显示10个
                stat = backup.stat()
                time_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size = stat.st_size
                size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
                print(f"  {backup.name} ({size_str}, {time_str})")
            if len(backups) > 10:
                print(f"  ... 还有 {len(backups) - 10} 个备份")
        else:
            print(f"\n[文件复制备份] 暂无 (目录: {FILE_BACKUP_DIR}/)")
    else:
        print(f"\n[文件复制备份] 暂无 (目录: {FILE_BACKUP_DIR}/)")


def cmd_rollback(filepath: str | None, git_branch: str | None = None, dry_run: bool = False) -> None:
    """从备份恢复文件

    参数:
        filepath: 要恢复的文件路径（用于 Git 备份匹配）
        git_branch: 指定的 Git 备份分支（None 表示自动选择）
        dry_run: 模拟模式
    """
    if dry_run:
        print(f"[DRY-RUN] 模拟恢复文件")
        if git_branch:
            print(f"[DRY-RUN] 将从 Git 分支恢复: {git_branch}")
        return

    # 先尝试从 Git 恢复
    if is_git_repo():
        target_branch = git_branch
        if target_branch is None:
            branches = get_backup_branches()
            if branches:
                target_branch = branches[0]

        if target_branch:
            verify = run_git("rev-parse", "--verify", target_branch)
            if verify.returncode == 0:
                # 获取该分支中的文件列表
                files_result = run_git(
                    "diff-tree", "--no-commit-id", "--name-only", "-r", target_branch
                )
                if files_result.returncode == 0 and files_result.stdout.strip():
                    files = files_result.stdout.strip().split("\n")
                    restored = 0
                    for f in files:
                        checkout_result = run_git("checkout", target_branch, "--", f)
                        if checkout_result.returncode == 0:
                            restored += 1
                            print(f"[OK] 从 Git 分支恢复: {f}")
                        else:
                            print(f"[WARN] 恢复失败: {f}")
                    if restored > 0:
                        print(f"[OK] 已从 Git 备份 {target_branch} 恢复 {restored} 个文件")
                        return

    # Git 恢复失败，尝试文件备份恢复
    if filepath:
        backups = get_file_backups(filepath)
        if backups:
            latest_backup = backups[0]
            try:
                shutil.copy2(latest_backup, filepath)
                print(f"[OK] 从文件备份恢复: {filepath}")
                print(f"       来源: {latest_backup.name}")
                return
            except Exception as e:
                print(f"[WARN] 文件恢复失败: {e}")

    print("[WARN] 未找到可恢复的备份")


def cmd_diff(filepath: str) -> None:
    """显示文件与最近备份的差异"""
    if not Path(filepath).exists():
        print(f"[WARN] 文件不存在: {filepath}")
        return

    # 先尝试 Git 备份比较
    if is_git_repo():
        branches = get_backup_branches()
        if branches:
            latest_branch = branches[0]
            result = run_git("diff", latest_branch, "--", filepath)
            if result.returncode == 0:
                if result.stdout.strip():
                    print(f"与 Git 备份 {latest_branch} 的差异：")
                    print(result.stdout)
                else:
                    print(f"[INFO] {filepath} 与 Git 备份 {latest_branch} 无差异")
                return

    # Git 比较失败，尝试文件备份
    backups = get_file_backups(filepath)
    if backups:
        latest_backup = backups[0]
        print(f"[INFO] 与文件备份 {latest_backup.name} 的差异：")
        print(f"[INFO] 文件备份不支持 diff 对比，请手动比较")
        print(f"       当前文件: {filepath}")
        print(f"       备份文件: {latest_backup}")
    else:
        print("[INFO] 未找到任何备份")


def cmd_cleanup(skip_confirm: bool = False, dry_run: bool = False) -> None:
    """删除所有备份（Git 分支 + 文件复制）"""
    if dry_run:
        print("[DRY-RUN] 模拟清理所有备份")
        return

    git_count = 0
    file_count = 0

    # 清理 Git 备份
    if is_git_repo():
        branches = get_backup_branches()
        if branches:
            if not skip_confirm:
                print(f"将删除 {len(branches)} 个 Git 备份分支：")
                for b in branches[:5]:
                    print(f"  {b}")
                if len(branches) > 5:
                    print(f"  ... 还有 {len(branches) - 5} 个")

    # 清理文件备份
    backup_dir = get_file_backup_dir()
    if backup_dir.exists():
        files = [f for f in backup_dir.iterdir() if f.is_file()]
        if files:
            if not skip_confirm:
                print(f"\n将删除 {len(files)} 个文件备份：")
                for f in files[:5]:
                    print(f"  {f.name}")
                if len(files) > 5:
                    print(f"  ... 还有 {len(files) - 5} 个")

    if not skip_confirm:
        try:
            answer = input("\n确认删除？(y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer != "y":
            print("[INFO] 已取消清理")
            return

    # 执行清理
    if is_git_repo():
        branches = get_backup_branches()
        for b in branches:
            result = run_git("branch", "-D", b)
            if result.returncode == 0:
                git_count += 1

    if backup_dir.exists():
        for f in backup_dir.iterdir():
            if f.is_file():
                try:
                    f.unlink()
                    file_count += 1
                except OSError:
                    pass

    print(f"[OK] 已删除 {git_count} 个 Git 备份分支，{file_count} 个文件备份")


# ── 入口 ──────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="engineering-paper-humanizer 智能备份脚本\n"
                    "支持 Git 分支备份（首选）和文件复制备份（回退）",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="列出所有备份")
    group.add_argument(
        "--rollback",
        nargs="?",
        const="__latest__",
        metavar="BRANCH",
        help="从最近备份或指定备份分支恢复文件",
    )
    group.add_argument("--diff", metavar="FILE", help="显示文件与最近备份的差异")
    group.add_argument("--cleanup", action="store_true", help="删除所有备份")

    parser.add_argument("--yes", action="store_true", help="跳过 --cleanup 的确认提示")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="模拟执行，显示将要进行的操作而不实际修改"
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="要备份的文件路径",
    )

    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.rollback is not None:
        target = None if args.rollback == "__latest__" else args.rollback
        cmd_rollback(args.file, target, dry_run=args.dry_run)
    elif args.diff:
        cmd_diff(args.diff)
    elif args.cleanup:
        cmd_cleanup(skip_confirm=args.yes, dry_run=args.dry_run)
    elif args.file:
        cmd_snapshot(args.file, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
