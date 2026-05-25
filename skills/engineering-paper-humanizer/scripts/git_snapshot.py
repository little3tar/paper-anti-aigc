#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文工作流智能备份脚本

规范源：skills/thesis-writing-workflow/scripts/git_snapshot.py
本文件为规范源的完整副本，修改规范源时需同步更新本文件。

智能备份策略（按优先级）：
1. Git 分支备份 - 当前目录已经是 Git 仓库且已有提交时使用
2. 文件复制备份 - 非 Git 目录、空 Git 仓库或 Git 不可用时使用 `.thesis-workflow/backups/`

备份保留策略：
- 默认保留最近 5 个普通备份，超出自动淘汰（可通过环境变量或参数调整）。
- 锚点备份（--anchor / --keep）永不自动淘汰，不受 MAX_BACKUPS 限制。
- 内容去重：与所有已有备份对比，内容相同时跳过（不产生重复版本）。
- 手动 --cleanup 会清理所有备份（含锚点），需交互确认。

用法:
python3 git_snapshot.py main.tex              # 创建备份
python3 git_snapshot.py main.tex --anchor     # 创建锚点备份（永不自动淘汰）
python3 git_snapshot.py --list                # 列出所有备份
python3 git_snapshot.py --rollback main.tex   # 从最近备份恢复指定文件
python3 git_snapshot.py --rollback --branch <name> main.tex  # 从指定分支恢复
python3 git_snapshot.py --diff main.tex       # 对比差异
python3 git_snapshot.py --cleanup             # 清理所有备份（需确认）
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from _shared import setup_windows_utf8

setup_windows_utf8()

BACKUP_PREFIX = "backup/thesis/"
FILE_BACKUP_DIR = Path(".thesis-workflow") / "backups"
ANCHOR_SUFFIX = ".anchor"  # 锚点标记文件后缀


def _resolve_max_backups(cli_value: int | None = None) -> int:
    """解析最大备份数：CLI 参数 > 环境变量 > 默认值 5。"""
    if cli_value is not None:
        return max(1, cli_value)
    try:
        return max(1, int(os.environ.get("GIT_SNAPSHOT_MAX_BACKUPS", "5")))
    except ValueError:
        return 5


def _resolve_workflow_root() -> Path:
    """解析论文工作流根目录（用于文件备份路径）。

    优先级：THESIS_WORKFLOW_DIR 环境变量 > Git 仓库根 > 当前目录。
    确保无论从哪个子目录运行脚本，备份都落到一致的位置。
    """
    env_dir = os.environ.get("THESIS_WORKFLOW_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except (FileNotFoundError, OSError):
        pass
    return Path.cwd()


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


def get_backup_branches() -> list[str]:
    """获取所有备份分支名，按时间倒序（最新在前）"""
    result = run_git(
        "branch", "--list", f"{BACKUP_PREFIX}*", "--format=%(refname:short)"
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    branches = result.stdout.strip().split("\n")
    branches.sort(reverse=True)
    return branches


def ensure_git_ready() -> dict:
    """确保 Git 环境就绪，返回状态字典"""
    status = {
        "available": is_git_available(),
        "is_repo": is_git_repo(),
        "ready": False,
        "mode": "file",
    }
    if not status["available"]:
        print("[INFO] Git 未安装或不可用，将使用文件复制备份")
        return status
    if status["is_repo"]:
        status["ready"] = True
        status["mode"] = "git"
        return status
    print("[INFO] 当前目录不是 Git 仓库，将使用文件复制备份")
    return status


def get_file_backup_dir() -> Path:
    """获取文件备份目录路径（统一基于工作流根目录）。"""
    return _resolve_workflow_root() / FILE_BACKUP_DIR


def _file_backup_glob_pattern(filepath: str) -> str:
    """为指定文件构造安全的备份文件 glob 模式。

    处理了无扩展名文件的边界情况：使用后缀精确锚定，
    避免 'README_*' 误匹配 'README_notes.txt'。
    """
    path = Path(filepath)
    stem = path.stem
    suffix = path.suffix  # 含前导点，如 ".tex"；无扩展名时为空
    if suffix:
        return f"{stem}_*{suffix}"
    else:
        # 无扩展名：要求备份文件名正好是 stem_<timestamp> 形态
        return f"{stem}_????????-??????"


def get_file_backups(filepath: str) -> list[Path]:
    """获取指定文件的所有文件备份，按时间倒序（最新在前）。"""
    backup_dir = get_file_backup_dir()
    if not backup_dir.exists():
        return []
    pattern = _file_backup_glob_pattern(filepath)
    backups = sorted(backup_dir.glob(pattern), reverse=True)
    # 过滤掉锚点标记文件
    backups = [b for b in backups if not b.name.endswith(ANCHOR_SUFFIX)]
    return backups


def _get_anchor_path(backup_path: Path) -> Path:
    """返回锚点标记文件路径。"""
    return backup_path.with_name(backup_path.name + ANCHOR_SUFFIX)


def _is_anchored(backup_path: Path) -> bool:
    """检查备份是否有锚点标记。"""
    return _get_anchor_path(backup_path).exists()


def _set_anchor(backup_path: Path) -> None:
    """为备份创建锚点标记。"""
    _get_anchor_path(backup_path).touch()


def _remove_anchor(backup_path: Path) -> None:
    """移除备份的锚点标记。"""
    anchor = _get_anchor_path(backup_path)
    try:
        anchor.unlink()
    except OSError:
        pass


def _is_git_branch_anchored(branch_name: str) -> bool:
    """通过分支名中的特殊标记判断是否为锚点备份。"""
    return "-anchor-" in branch_name


def _content_hash(data: bytes) -> str:
    """计算内容的 SHA-256 哈希（十六进制）。"""
    return hashlib.sha256(data).hexdigest()


def _file_content_hash(filepath: Path) -> str:
    """读取文件并计算其内容的 SHA-256 哈希。"""
    return _content_hash(filepath.read_bytes())


# ── 文件复制备份功能 ─────────────────────────────────────────


def file_backup(filepath: str, max_backups: int, anchor: bool = False,
                dry_run: bool = False) -> bool:
    """使用文件复制备份文件。

    参数:
        filepath: 要备份的文件路径
        max_backups: 最大保留备份数
        anchor: 是否创建锚点备份（永不自动淘汰）
        dry_run: 模拟模式

    返回:
        备份是否成功
    """
    if dry_run:
        print(f"[DRY-RUN] 模拟文件备份: {filepath}")
        if anchor:
            print(f"[DRY-RUN]   标记为锚点备份（永不自动淘汰）")
        print(f"[DRY-RUN]   最大保留: {max_backups}")
        return True

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过备份")
        return False

    backup_dir = get_file_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 与所有已有备份去重（非仅最近一次）
    current_hash = _file_content_hash(path)
    all_backups = get_file_backups(filepath)
    for existing in all_backups:
        if _file_content_hash(existing) == current_hash:
            print(f"[INFO] {filepath} 与已有备份 {existing.name} 内容相同，跳过备份")
            return True

    # 创建带时间戳的备份文件（厘秒精度，避免秒级冲突）
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:18]  # 截断微秒到厘秒（2位）
    filename = f"{path.stem}_{timestamp}{path.suffix}"
    backup_path = backup_dir / filename

    try:
        shutil.copy2(path, backup_path)
        print(f"[OK] 已创建文件备份: {backup_path.relative_to(Path.cwd())}")
    except Exception as e:
        print(f"[WARN] 文件备份失败: {e}")
        return False

    if anchor:
        _set_anchor(backup_path)
        print(f"[OK]   已标记为锚点备份")

    # 自动淘汰旧备份（跳过锚点）
    _auto_evict_file_backups(filepath, max_backups)
    return True


def _auto_evict_file_backups(filepath: str, max_backups: int) -> None:
    """删除超出限制的旧文件备份（锚点备份除外）。"""
    backups = get_file_backups(filepath)
    # 按锚点 / 非锚点分拆
    anchored = [b for b in backups if _is_anchored(b)]
    regular = [b for b in backups if not _is_anchored(b)]
    if len(regular) <= max_backups:
        return
    to_delete = regular[max_backups:]
    for backup in to_delete:
        try:
            backup.unlink()
            _remove_anchor(backup)  # 清理可能的残留锚点
            print(f"[INFO] 自动淘汰旧文件备份: {backup.name}")
        except OSError as e:
            print(f"[WARN] 删除旧备份失败 {backup.name}: {e}")


# ── Git 分支备份功能 ─────────────────────────────────────────


def _git_rel_path(filepath: str) -> str | None:
    """获取文件在 Git 仓库中的相对路径。"""
    path = Path(filepath).resolve()
    try:
        root_result = run_git("rev-parse", "--show-toplevel")
        if root_result.returncode != 0:
            return None
        root = Path(root_result.stdout.strip()).resolve()
        return path.relative_to(root).as_posix()
    except (ValueError, OSError):
        return None


def _git_blob_hash(filepath: str) -> str | None:
    """获取文件中已存在于 Git 对象库的 blob hash。"""
    path = Path(filepath)
    result = run_git("hash-object", str(path))
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _git_branch_content_hash(branch: str, rel_path: str) -> str | None:
    """获取 Git 分支中指定文件内容的 SHA-256。"""
    result = run_git("show", f"{branch}:{rel_path}")
    if result.returncode == 0:
        return _content_hash(result.stdout.encode("utf-8"))
    return None


def git_backup(filepath: str, max_backups: int, anchor: bool = False,
               dry_run: bool = False) -> bool:
    """使用 Git 分支备份单个文件。

    技术说明：这里创建的备份分支存储了基于当前 HEAD tree 的完整仓库快照
    （仅目标文件被替换为新 blob），这样 git diff 等操作可以正常工作。
    但回滚时只会恢复目标文件，不会影响其他文件。

    参数:
        filepath: 要备份的文件路径
        max_backups: 最大保留备份数
        anchor: 是否创建锚点备份
        dry_run: 模拟模式

    返回:
        备份是否成功
    """
    if dry_run:
        print(f"[DRY-RUN] 模拟 Git 备份: {filepath}")
        if anchor:
            print(f"[DRY-RUN]   标记为锚点备份（永不自动淘汰）")
        print(f"[DRY-RUN]   最大保留: {max_backups}")
        return True

    if not is_git_repo():
        print("[WARN] Git 仓库不可用，无法创建分支备份")
        return False

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过分支备份")
        return False

    # 空仓库检测
    head_check = run_git("rev-parse", "--verify", "HEAD")
    if head_check.returncode != 0:
        print("[WARN] 仓库尚无任何提交，请先执行 git commit 后再使用 Git 备份功能")
        print("[INFO] 将尝试文件复制备份作为替代...")
        return False

    rel_path = _git_rel_path(filepath)
    if rel_path is None:
        print(f"[WARN] 文件 {filepath} 不在仓库内")
        return False

    # 与所有已有分支备份去重
    new_blob = _git_blob_hash(filepath)
    if new_blob:
        for branch in get_backup_branches():
            old_blob_result = run_git("rev-parse", f"{branch}:{rel_path}")
            if old_blob_result.returncode == 0:
                if old_blob_result.stdout.strip() == new_blob:
                    print(f"[INFO] {filepath} 与已有 Git 备份 {branch} 内容相同，跳过备份")
                    return True

    # 创建备份分支
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:18]
    anchor_tag = "-anchor" if anchor else ""
    backup_branch = f"{BACKUP_PREFIX}{timestamp}{anchor_tag}"

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
        r = subprocess.run(
            ["git", "read-tree", head_tree],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        if r.returncode != 0:
            print(f"[WARN] read-tree 失败：{r.stderr.strip()}")
            return False

        r = subprocess.run(
            ["git", "update-index", "--add", "--cacheinfo",
             f"100644,{blob_hash},{rel_path}"],
            capture_output=True, text=True, encoding="utf-8", env=env,
        )
        if r.returncode != 0:
            print(f"[WARN] update-index 失败：{r.stderr.strip()}")
            return False

        r = subprocess.run(
            ["git", "write-tree"],
            capture_output=True, text=True, encoding="utf-8", env=env,
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

    commit_msg = f"[backup] {path.name} @ {timestamp}"
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
    if anchor:
        print(f"[OK]   已标记为锚点备份")

    # 自动淘汰旧备份
    _auto_evict_old_git_backups(max_backups)
    return True


def _auto_evict_old_git_backups(max_backups: int) -> None:
    """当非锚点备份分支数超过 max_backups 时，自动删除最旧的。"""
    branches = get_backup_branches()
    anchored = [b for b in branches if _is_git_branch_anchored(b)]
    regular = [b for b in branches if not _is_git_branch_anchored(b)]
    if len(regular) <= max_backups:
        return
    to_delete = regular[max_backups:]
    for b in to_delete:
        result = run_git("branch", "-D", b)
        if result.returncode == 0:
            print(f"[INFO] 自动淘汰旧 Git 备份：{b}")


# ── 统一的备份入口 ───────────────────────────────────────────


def cmd_snapshot(filepath: str, max_backups: int, anchor: bool = False,
                 dry_run: bool = False) -> None:
    """智能备份入口 - 优先 Git 分支备份，回退到文件复制。"""
    if dry_run:
        print(f"[DRY-RUN] 模拟备份文件: {filepath}")
        print("=" * 50)

    status = ensure_git_ready()
    if status["mode"] == "git" and status["ready"]:
        if git_backup(filepath, max_backups, anchor=anchor, dry_run=dry_run):
            return
        print("[INFO] Git 备份失败，尝试文件备份...")
    else:
        print("[INFO] 未满足 Git 分支备份条件，改用文件复制备份")

    file_backup(filepath, max_backups, anchor=anchor, dry_run=dry_run)


# ── 其他命令功能 ─────────────────────────────────────────────


def cmd_list() -> None:
    """列出所有备份（Git 分支 + 文件复制）。"""
    print("=" * 50)
    print("备份列表")
    print("=" * 50)

    # 列出 Git 备份
    if is_git_repo():
        branches = get_backup_branches()
        if branches:
            print(f"\n[Git 分支备份] 共 {len(branches)} 个（最新在前）：")
            for branch in branches:
                anchor_mark = " [锚点]" if _is_git_branch_anchored(branch) else ""
                log_result = run_git("log", branch, "-1", "--format=%ai %s")
                info = log_result.stdout.strip() if log_result.returncode == 0 else ""
                print(f"  {branch}{anchor_mark}")
                if info:
                    print(f"    └─ {info}")
        else:
            print("\n[Git 分支备份] 暂无")
    else:
        print("\n[Git 分支备份] Git 仓库不可用")

    # 列出文件备份
    backup_dir = get_file_backup_dir()
    if backup_dir.exists():
        all_files = sorted(
            [f for f in backup_dir.iterdir() if f.is_file() and not f.name.endswith(ANCHOR_SUFFIX)],
            reverse=True,
        )
        if all_files:
            print(f"\n[文件复制备份] 目录: {FILE_BACKUP_DIR.as_posix()}/")
            print(f"               共 {len(all_files)} 个（最新在前）：")
            for backup in all_files[:10]:
                anchor_mark = " [锚点]" if _is_anchored(backup) else ""
                stat = backup.stat()
                time_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size = stat.st_size
                size_str = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"
                print(f"  {backup.name} ({size_str}, {time_str}){anchor_mark}")
            if len(all_files) > 10:
                print(f"  ... 还有 {len(all_files) - 10} 个备份")
        else:
            print(f"\n[文件复制备份] 暂无 (目录: {FILE_BACKUP_DIR.as_posix()}/)")
    else:
        print(f"\n[文件复制备份] 暂无 (目录: {FILE_BACKUP_DIR.as_posix()}/)")


def cmd_rollback(filepath: str | None, git_branch: str | None = None,
                 dry_run: bool = False, skip_confirm: bool = False) -> None:
    """从备份恢复指定文件。

    重要：Git 模式只恢复目标文件（使用 git show），不会恢复整个分支快照。
    文件模式从文件备份复制。

    参数:
        filepath: 要恢复的文件路径
        git_branch: 指定的 Git 备份分支（None = 自动选择最近的）
        dry_run: 模拟模式
        skip_confirm: 跳过确认提示
    """
    if dry_run:
        print(f"[DRY-RUN] 模拟恢复文件")
        if filepath:
            print(f"[DRY-RUN]   目标文件: {filepath}")
        if git_branch:
            print(f"[DRY-RUN]   从 Git 分支: {git_branch}")
        return

    if filepath is None:
        print("[WARN] --rollback 需要指定要恢复的目标文件")
        print("用法: git_snapshot.py --rollback <文件路径>")
        print("      git_snapshot.py --rollback --branch <分支名> <文件路径>")
        return

    target_path = Path(filepath)

    # 先尝试 Git 恢复（仅恢复目标文件）
    if is_git_repo():
        target_branch = git_branch
        if target_branch is None:
            branches = get_backup_branches()
            if branches:
                target_branch = branches[0]

        if target_branch:
            verify = run_git("rev-parse", "--verify", target_branch)
            if verify.returncode == 0:
                rel_path = _git_rel_path(filepath)
                if rel_path is None:
                    print(f"[WARN] 文件 {filepath} 不在 Git 仓库内")
                else:
                    # 确认该分支中存在此文件
                    check = run_git("cat-file", "-e", f"{target_branch}:{rel_path}")
                    if check.returncode != 0:
                        print(f"[WARN] Git 备份 {target_branch} 中不包含文件 {rel_path}")
                    else:
                        # 安全确认
                        if not skip_confirm:
                            print(f"将从 Git 备份恢复文件:")
                            print(f"  分支: {target_branch}")
                            print(f"  目标文件: {filepath}")
                            print(f"  （仅恢复此文件，不影响工作区其他文件）")
                            try:
                                answer = input("\n确认恢复？(y/N): ").strip().lower()
                            except (EOFError, KeyboardInterrupt):
                                answer = ""
                            if answer != "y":
                                print("[INFO] 已取消恢复")
                                return

                        # 使用 git show 仅恢复目标文件
                        blob_result = run_git("show", f"{target_branch}:{rel_path}")
                        if blob_result.returncode != 0:
                            print(f"[WARN] 读取备份文件内容失败")
                            return
                        try:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            target_path.write_bytes(blob_result.stdout.encode("utf-8"))
                            print(f"[OK] 已从 Git 备份 {target_branch} 恢复: {filepath}")
                            return
                        except OSError as e:
                            print(f"[WARN] 写入文件失败: {e}")
                            return

    # Git 恢复失败，尝试文件备份恢复
    backups = get_file_backups(filepath)
    if backups:
        latest_backup = backups[0]

        if not skip_confirm:
            print(f"将从文件备份恢复:")
            print(f"  备份文件: {latest_backup}")
            print(f"  目标文件: {filepath}")
            try:
                answer = input("\n确认恢复？(y/N): ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer != "y":
                print("[INFO] 已取消恢复")
                return

        try:
            shutil.copy2(latest_backup, filepath)
            print(f"[OK] 从文件备份恢复: {filepath}")
            print(f"       来源: {latest_backup.name}")
            return
        except Exception as e:
            print(f"[WARN] 文件恢复失败: {e}")

    print("[WARN] 未找到可恢复的备份")


def cmd_diff(filepath: str) -> None:
    """显示文件与最近备份的差异。"""
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
    """删除所有备份（Git 分支 + 文件复制），包括锚点备份。"""
    if dry_run:
        print("[DRY-RUN] 模拟清理所有备份")
        return

    git_count = 0
    file_count = 0

    # 统计 Git 备份
    if is_git_repo():
        branches = get_backup_branches()
        if branches:
            anchored_branches = [b for b in branches if _is_git_branch_anchored(b)]
            if not skip_confirm:
                print(f"将删除 {len(branches)} 个 Git 备份分支：")
                for b in branches[:5]:
                    mark = " [锚点]" if b in anchored_branches else ""
                    print(f"  {b}{mark}")
                if len(branches) > 5:
                    print(f"  ... 还有 {len(branches) - 5} 个")
                if anchored_branches:
                    print(f"  其中包含 {len(anchored_branches)} 个锚点备份")

    # 统计文件备份
    backup_dir = get_file_backup_dir()
    if backup_dir.exists():
        all_files = [f for f in backup_dir.iterdir() if f.is_file()]
        anchored_files = [f for f in all_files if _is_anchored(f)]
        if all_files:
            if not skip_confirm:
                bak_files = [f for f in all_files if not f.name.endswith(ANCHOR_SUFFIX)]
                print(f"\n将删除 {len(bak_files)} 个文件备份：")
                for f in bak_files[:5]:
                    mark = " [锚点]" if f in anchored_files else ""
                    print(f"  {f.name}{mark}")
                if len(bak_files) > 5:
                    print(f"  ... 还有 {len(bak_files) - 5} 个")
                if anchored_files:
                    print(f"  其中包含 {len(anchored_files)} 个锚点备份")

    if not skip_confirm:
        try:
            answer = input("\n确认删除所有备份（含锚点）？(y/N): ").strip().lower()
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
        description="论文工作流智能备份脚本 — Git 分支备份优先，文件复制兜底",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="列出所有备份")
    group.add_argument(
        "--rollback",
        nargs="?",
        const="__latest__",
        metavar="BRANCH",
        help="从最近备份或指定备份分支恢复文件（需指定目标文件）",
    )
    group.add_argument("--diff", metavar="FILE", help="显示文件与最近备份的差异")
    group.add_argument("--cleanup", action="store_true", help="删除所有备份")

    parser.add_argument("--yes", action="store_true", help="跳过确认提示")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="模拟执行，显示将要进行的操作而不实际修改",
    )
    parser.add_argument(
        "--anchor", "--keep", dest="anchor", action="store_true",
        help="创建锚点备份（永不自动淘汰，除非手动 --cleanup）",
    )
    parser.add_argument(
        "--max-backups", metavar="N", type=int, default=None,
        help="最大保留的普通备份数（默认 5，可通过 GIT_SNAPSHOT_MAX_BACKUPS 环境变量设置）",
    )
    parser.add_argument(
        "--branch", metavar="BRANCH", type=str, default=None,
        help="与 --rollback 配合使用，指定要恢复的 Git 备份分支",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="要备份的目标文件路径",
    )

    args = parser.parse_args()
    max_backups = _resolve_max_backups(args.max_backups)

    if args.list:
        cmd_list()
    elif args.rollback is not None:
        target_branch = None if args.rollback == "__latest__" else args.rollback
        # 如果 --branch 也被指定，优先使用 --branch
        if args.branch:
            target_branch = args.branch
        cmd_rollback(args.file, target_branch, dry_run=args.dry_run, skip_confirm=args.yes)
    elif args.diff:
        cmd_diff(args.diff)
    elif args.cleanup:
        cmd_cleanup(skip_confirm=args.yes, dry_run=args.dry_run)
    elif args.file:
        cmd_snapshot(args.file, max_backups, anchor=args.anchor, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
