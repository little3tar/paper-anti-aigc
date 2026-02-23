#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""engineering-paper-humanizer Git 安全快照脚本

在修改 .tex 文件之前自动创建 Git 备份快照，支持查看历史、回滚和对比差异。
非 Git 环境下自动跳过，不影响任何现有功能。

用法:
    python3 scripts/git_snapshot.py main.tex           # 创建备份快照
    python3 scripts/git_snapshot.py --list             # 列出所有备份快照
    python3 scripts/git_snapshot.py --rollback         # 回滚到最近快照
    python3 scripts/git_snapshot.py --rollback abc1234 # 回滚到指定快照
    python3 scripts/git_snapshot.py --diff main.tex    # 对比与最近快照的差异
"""

import argparse
import subprocess
from pathlib import Path
import sys
import io
import os

# Windows GBK 终端兼容：强制 UTF-8 输出
if os.name == 'nt':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


SNAPSHOT_PREFIX = "[humanizer-backup]"
SNAPSHOT_GREP = r"\[humanizer-backup\]"


# ── Git 环境检测 ───────────────────────────────────────────

def is_git_repo() -> bool:
    """检测当前目录是否处于 Git 仓库内"""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True, encoding='utf-8'
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_latest_snapshot_hash() -> str | None:
    """获取最近一次备份快照的 commit hash"""
    result = subprocess.run(
        ["git", "log", "--format=%H", f"--grep={SNAPSHOT_GREP}", "-1"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


# ── 核心功能 ───────────────────────────────────────────────

def cmd_snapshot(filepath: str) -> None:
    """为指定文件创建备份快照提交"""
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，跳过备份快照（不影响后续流程）")
        return

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过备份快照")
        return

    # 检查文件是否有未提交变更
    status_result = subprocess.run(
        ["git", "status", "--porcelain", str(path)],
        capture_output=True, text=True, encoding='utf-8'
    )
    has_changes = bool(status_result.stdout.strip())

    if has_changes:
        # 有变更：git add + git commit
        subprocess.run(["git", "add", str(path)], check=True, encoding='utf-8')
        commit_msg = f"{SNAPSHOT_PREFIX} 修改前备份 {path.name}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True, text=True, encoding='utf-8'
        )
        if result.returncode == 0:
            print(f"[OK] 已创建备份快照：{commit_msg}")
        else:
            print(f"[WARN] 创建快照失败：{result.stderr.strip()}")
    else:
        # 无变更：检查最近提交是否已是备份快照
        latest_msg_result = subprocess.run(
            ["git", "log", "--format=%s", "-1"],
            capture_output=True, text=True, encoding='utf-8'
        )
        latest_msg = (latest_msg_result.stdout or '').strip()
        if latest_msg.startswith(SNAPSHOT_PREFIX):
            print("[INFO] 文件无变更且最近提交已是备份快照，跳过")
        else:
            # 创建空提交作为标记点
            commit_msg = f"{SNAPSHOT_PREFIX} 无变更标记点 {path.name}"
            result = subprocess.run(
                ["git", "commit", "--allow-empty", "-m", commit_msg],
                capture_output=True, text=True, encoding='utf-8'
            )
            if result.returncode == 0:
                print(f"[OK] 已创建空提交标记点：{commit_msg}")
            else:
                print(f"[WARN] 创建标记点失败：{result.stderr.strip()}")


def cmd_list() -> None:
    """列出所有备份快照"""
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，无法列出备份快照")
        return

    result = subprocess.run(
        ["git", "log", "--format=%h %ai %s", f"--grep={SNAPSHOT_GREP}"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        print(f"[WARN] 查询失败：{result.stderr.strip()}")
        return

    snapshots = result.stdout.strip()
    if not snapshots:
        print("[INFO] 暂无备份快照记录")
    else:
        print("备份快照列表（最新在前）：")
        print(snapshots)


def cmd_rollback(target_hash: str | None) -> None:
    """回滚到指定快照（默认最近一次）"""
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，无法执行回滚")
        return

    if target_hash is None:
        target_hash = get_latest_snapshot_hash()
        if target_hash is None:
            print("[INFO] 未找到任何备份快照，无法回滚")
            return

    # 回滚前先自动保存当前状态（防止用户后悔回滚）
    pre_rollback_msg = f"{SNAPSHOT_PREFIX} 回滚前自动保存"
    subprocess.run(["git", "add", "-u"], capture_output=True, encoding='utf-8')
    save_result = subprocess.run(
        ["git", "commit", "--allow-empty", "-m", pre_rollback_msg],
        capture_output=True, text=True, encoding='utf-8'
    )
    if save_result.returncode == 0:
        print(f"[OK] 已保存当前状态：{pre_rollback_msg}")

    # 执行回滚
    checkout_result = subprocess.run(
        ["git", "checkout", target_hash, "--", "."],
        capture_output=True, text=True, encoding='utf-8'
    )
    if checkout_result.returncode == 0:
        print(f"[OK] 已回滚到快照：{target_hash}")
    else:
        print(f"[WARN] 回滚失败：{checkout_result.stderr.strip()}")


def cmd_diff(filepath: str) -> None:
    """显示文件与最近快照的差异"""
    if not is_git_repo():
        print("[WARN] 当前目录不在 Git 仓库内，无法对比差异")
        return

    snapshot_hash = get_latest_snapshot_hash()
    if snapshot_hash is None:
        print("[INFO] 未找到任何备份快照，无法对比差异")
        return

    result = subprocess.run(
        ["git", "diff", snapshot_hash, "--", filepath],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode != 0:
        print(f"[WARN] 对比失败：{result.stderr.strip()}")
        return

    if result.stdout.strip():
        print(result.stdout)
    else:
        print(f"[INFO] {filepath} 与最近快照 {snapshot_hash[:7]} 无差异")


# ── 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="engineering-paper-humanizer Git 安全快照"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--list", action="store_true",
        help="列出所有备份快照"
    )
    group.add_argument(
        "--rollback", nargs="?", const="__latest__", metavar="HASH",
        help="回滚到最近快照或指定 hash"
    )
    group.add_argument(
        "--diff", metavar="FILE",
        help="显示文件与最近快照的差异"
    )
    parser.add_argument(
        "file", nargs="?",
        help="要备份的 .tex 文件路径（不与 --list/--rollback/--diff 同用）"
    )
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.rollback is not None:
        target = None if args.rollback == "__latest__" else args.rollback
        cmd_rollback(target)
    elif args.diff:
        cmd_diff(args.diff)
    elif args.file:
        cmd_snapshot(args.file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
