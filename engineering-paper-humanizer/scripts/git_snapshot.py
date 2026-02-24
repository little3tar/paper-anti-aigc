#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engineering-paper-humanizer Git 分支备份脚本

在修改 .tex 文件之前，自动创建独立的备份分支保存当前文件状态，
不污染主分支的提交历史。支持列出备份、回滚、对比差异和清理旧备份。
非 Git 环境下自动跳过，不影响任何现有功能。

用法:
    python3 scripts/git_snapshot.py main.tex           # 创建分支备份
    python3 scripts/git_snapshot.py --list             # 列出所有备份分支
    python3 scripts/git_snapshot.py --rollback         # 从最近备份恢复文件
    python3 scripts/git_snapshot.py --rollback <branch># 从指定备份恢复文件
    python3 scripts/git_snapshot.py --diff main.tex    # 对比与最近备份的差异
    python3 scripts/git_snapshot.py --cleanup          # 删除所有备份分支（需确认）
    python3 scripts/git_snapshot.py --cleanup --yes    # 删除所有备份分支（跳过确认）
"""

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import sys
import io
import os

# Windows GBK 终端兼容：强制 UTF-8 输出
if os.name == 'nt':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


BACKUP_PREFIX = "backup/humanizer/"


# ── 工具函数 ───────────────────────────────────────────────

def run_git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """执行 git 命令并返回结果"""
    return subprocess.run(
        ["git", *args],
        capture_output=True, text=True, encoding='utf-8',
        check=check
    )


def is_git_repo() -> bool:
    """检测当前目录是否处于 Git 仓库内"""
    result = run_git("rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_current_branch() -> str | None:
    """获取当前分支名（detached HEAD 时返回 None）"""
    result = run_git("symbolic-ref", "--short", "HEAD")
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def get_backup_branches() -> list[str]:
    """获取所有备份分支名，按时间倒序（最新在前）"""
    result = run_git("branch", "--list", f"{BACKUP_PREFIX}*", "--format=%(refname:short)")
    if result.returncode != 0 or not result.stdout.strip():
        return []
    branches = result.stdout.strip().split('\n')
    branches.sort(reverse=True)  # 分支名含时间戳，字典序倒排即时间倒序
    return branches


def has_staged_or_unstaged_changes() -> bool:
    """检查工作区是否有未提交的变更（包括 staged 和 unstaged）"""
    result = run_git("status", "--porcelain")
    return bool(result.stdout.strip())


# ── 核心功能 ───────────────────────────────────────────────

def cmd_snapshot(filepath: str) -> None:
    """为指定文件创建备份分支

    流程：
    1. 记录当前分支
    2. stash 保存工作区变更（如有）
    3. 创建备份分支并提交目标文件
    4. 切回原分支
    5. 恢复 stash（如有）
    """
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，跳过分支备份（不影响后续流程）")
        return

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过分支备份")
        return

    # 记录当前分支
    original_branch = get_current_branch()
    if original_branch is None:
        print("[WARN] 当前处于 detached HEAD 状态，跳过分支备份")
        return

    # 生成备份分支名
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_branch = f"{BACKUP_PREFIX}{timestamp}"

    # stash 保存当前工作区变更
    had_changes = has_staged_or_unstaged_changes()
    if had_changes:
        stash_result = run_git("stash", "push", "-m", f"humanizer-backup-temp-{timestamp}")
        if stash_result.returncode != 0:
            print(f"[WARN] stash 失败：{stash_result.stderr.strip()}，跳过分支备份")
            return

    try:
        # 创建并切换到备份分支
        create_result = run_git("checkout", "-b", backup_branch)
        if create_result.returncode != 0:
            print(f"[WARN] 创建备份分支失败：{create_result.stderr.strip()}")
            return

        # 在备份分支上提交目标文件
        run_git("add", str(path))
        commit_msg = f"[humanizer-backup] {path.name} @ {timestamp}"
        commit_result = run_git("commit", "--allow-empty", "-m", commit_msg)
        if commit_result.returncode != 0:
            print(f"[WARN] 备份提交失败：{commit_result.stderr.strip()}")
            # 即使提交失败也需要切回原分支
        else:
            print(f"[OK] 已创建备份分支：{backup_branch}")

    finally:
        # 无论成功失败，都切回原分支
        switch_result = run_git("checkout", original_branch)
        if switch_result.returncode != 0:
            print(f"[ERROR] 切回原分支 {original_branch} 失败：{switch_result.stderr.strip()}")
            print("[ERROR] 请手动执行: git checkout", original_branch)

        # 恢复 stash
        if had_changes:
            pop_result = run_git("stash", "pop")
            if pop_result.returncode != 0:
                print(f"[WARN] stash pop 失败：{pop_result.stderr.strip()}")
                print("[WARN] 你的变更仍在 stash 中，请手动执行: git stash pop")


def cmd_list() -> None:
    """列出所有备份分支"""
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，无法列出备份分支")
        return

    branches = get_backup_branches()
    if not branches:
        print("[INFO] 暂无备份分支")
        return

    print(f"备份分支列表（共 {len(branches)} 个，最新在前）：")
    for branch in branches:
        # 获取该分支最新提交的信息
        log_result = run_git("log", branch, "-1", "--format=%ai %s")
        info = log_result.stdout.strip() if log_result.returncode == 0 else ""
        print(f"  {branch}  {info}")


def cmd_rollback(target_branch: str | None) -> None:
    """从备份分支恢复文件到当前工作区

    不切换分支，仅通过 git checkout <backup-branch> -- . 恢复文件内容。
    """
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，无法执行回滚")
        return

    # 未指定分支时，使用最近的备份
    if target_branch is None:
        branches = get_backup_branches()
        if not branches:
            print("[INFO] 未找到任何备份分支，无法回滚")
            return
        target_branch = branches[0]

    # 验证备份分支存在
    verify = run_git("rev-parse", "--verify", target_branch)
    if verify.returncode != 0:
        print(f"[WARN] 备份分支不存在：{target_branch}")
        return

    # 从备份分支恢复文件（不切换分支）
    checkout_result = run_git("checkout", target_branch, "--", ".")
    if checkout_result.returncode == 0:
        print(f"[OK] 已从备份分支恢复文件：{target_branch}")
    else:
        print(f"[WARN] 回滚失败：{checkout_result.stderr.strip()}")


def cmd_diff(filepath: str) -> None:
    """显示文件与最近备份分支的差异"""
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，无法对比差异")
        return

    branches = get_backup_branches()
    if not branches:
        print("[INFO] 未找到任何备份分支，无法对比差异")
        return

    latest_branch = branches[0]
    result = run_git("diff", latest_branch, "--", filepath)
    if result.returncode != 0:
        print(f"[WARN] 对比失败：{result.stderr.strip()}")
        return

    if result.stdout.strip():
        print(f"与备份分支 {latest_branch} 的差异：")
        print(result.stdout)
    else:
        print(f"[INFO] {filepath} 与最近备份 {latest_branch} 无差异")


def cmd_cleanup(skip_confirm: bool = False) -> None:
    """删除所有备份分支"""
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，无法清理备份分支")
        return

    branches = get_backup_branches()
    if not branches:
        print("[INFO] 暂无备份分支需要清理")
        return

    print(f"将删除以下 {len(branches)} 个备份分支：")
    for b in branches:
        print(f"  {b}")

    if not skip_confirm:
        try:
            answer = input("\n确认删除？(y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        if answer != 'y':
            print("[INFO] 已取消清理")
            return

    deleted = 0
    for b in branches:
        result = run_git("branch", "-D", b)
        if result.returncode == 0:
            deleted += 1
        else:
            print(f"[WARN] 删除失败: {b} — {result.stderr.strip()}")

    print(f"[OK] 已删除 {deleted}/{len(branches)} 个备份分支")


# ── 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="engineering-paper-humanizer Git 分支备份"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--list", action="store_true",
        help="列出所有备份分支"
    )
    group.add_argument(
        "--rollback", nargs="?", const="__latest__", metavar="BRANCH",
        help="从最近备份或指定备份分支恢复文件"
    )
    group.add_argument(
        "--diff", metavar="FILE",
        help="显示文件与最近备份分支的差异"
    )
    group.add_argument(
        "--cleanup", action="store_true",
        help="删除所有备份分支"
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="跳过 --cleanup 的确认提示"
    )
    parser.add_argument(
        "file", nargs="?",
        help="要备份的 .tex 文件路径（不与 --list/--rollback/--diff/--cleanup 同用）"
    )
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.rollback is not None:
        target = None if args.rollback == "__latest__" else args.rollback
        cmd_rollback(target)
    elif args.diff:
        cmd_diff(args.diff)
    elif args.cleanup:
        cmd_cleanup(skip_confirm=args.yes)
    elif args.file:
        cmd_snapshot(args.file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
