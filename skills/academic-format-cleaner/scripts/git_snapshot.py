#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文工作流智能备份脚本（format-cleaner 专用精简版）

规范源：skills/thesis-writing-workflow/scripts/git_snapshot.py（含全部命令）。
本副本仅包含 format-cleaner 实际使用的 cmd_snapshot 备份入口，不含 list/rollback/diff/cleanup。

智能备份策略（按优先级）：
1. Git 分支备份 - 当前目录已经是 Git 仓库且已有提交时使用
2. 文件复制备份 - 非 Git 目录、空 Git 仓库或 Git 不可用时使用 .thesis-workflow/backups/

备份保留策略：
- 锚点备份（--anchor）永不自动淘汰，不受 max_backups 限制。
- 内容去重：与所有已有备份对比，内容相同时跳过。
- 普通备份超出限制时自动淘汰（可通过环境变量或参数调整）。

用法:
python3 git_snapshot.py main.tex              # 创建备份
python3 git_snapshot.py main.tex --anchor     # 创建锚点备份（永不自动淘汰）
"""

from __future__ import annotations

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
ANCHOR_SUFFIX = ".anchor"


def _resolve_max_backups(cli_value: int | None = None) -> int:
    if cli_value is not None:
        return max(1, cli_value)
    try:
        return max(1, int(os.environ.get("GIT_SNAPSHOT_MAX_BACKUPS", "5")))
    except ValueError:
        return 5


def _resolve_workflow_root() -> Path:
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
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", check=check
    )


def is_git_available() -> bool:
    try:
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, encoding="utf-8"
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def is_git_repo() -> bool:
    result = run_git("rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def get_backup_branches() -> list[str]:
    result = run_git(
        "branch", "--list", f"{BACKUP_PREFIX}*", "--format=%(refname:short)"
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    branches = result.stdout.strip().split("\n")
    branches.sort(reverse=True)
    return branches


def ensure_git_ready() -> dict:
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
    return _resolve_workflow_root() / FILE_BACKUP_DIR


def _file_backup_glob_pattern(filepath: str) -> str:
    path = Path(filepath)
    stem = path.stem
    suffix = path.suffix
    if suffix:
        return f"{stem}_*{suffix}"
    else:
        return f"{stem}_????????-??????"


def get_file_backups(filepath: str) -> list[Path]:
    backup_dir = get_file_backup_dir()
    if not backup_dir.exists():
        return []
    pattern = _file_backup_glob_pattern(filepath)
    backups = sorted(backup_dir.glob(pattern), reverse=True)
    backups = [b for b in backups if not b.name.endswith(ANCHOR_SUFFIX)]
    return backups


def _get_anchor_path(backup_path: Path) -> Path:
    return backup_path.with_name(backup_path.name + ANCHOR_SUFFIX)


def _is_anchored(backup_path: Path) -> bool:
    return _get_anchor_path(backup_path).exists()


def _set_anchor(backup_path: Path) -> None:
    _get_anchor_path(backup_path).touch()


def _remove_anchor(backup_path: Path) -> None:
    anchor = _get_anchor_path(backup_path)
    try:
        anchor.unlink()
    except OSError:
        pass


def _is_git_branch_anchored(branch_name: str) -> bool:
    return "-anchor-" in branch_name


def _content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_content_hash(filepath: Path) -> str:
    return _content_hash(filepath.read_bytes())


# ── 文件复制备份功能 ─────────────────────────────────────────


def file_backup(filepath: str, max_backups: int, anchor: bool = False,
                dry_run: bool = False) -> bool:
    if dry_run:
        print(f"[DRY-RUN] 模拟文件备份: {filepath}")
        if anchor:
            print(f"[DRY-RUN]   标记为锚点备份")
        print(f"[DRY-RUN]   最大保留: {max_backups}")
        return True

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过备份")
        return False

    backup_dir = get_file_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    current_hash = _file_content_hash(path)
    all_backups = get_file_backups(filepath)
    for existing in all_backups:
        if _file_content_hash(existing) == current_hash:
            print(f"[INFO] {filepath} 与已有备份 {existing.name} 内容相同，跳过备份")
            return True

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:18]
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

    _auto_evict_file_backups(filepath, max_backups)
    return True


def _auto_evict_file_backups(filepath: str, max_backups: int) -> None:
    backups = get_file_backups(filepath)
    anchored = [b for b in backups if _is_anchored(b)]
    regular = [b for b in backups if not _is_anchored(b)]
    if len(regular) <= max_backups:
        return
    to_delete = regular[max_backups:]
    for backup in to_delete:
        try:
            backup.unlink()
            _remove_anchor(backup)
            print(f"[INFO] 自动淘汰旧文件备份: {backup.name}")
        except OSError as e:
            print(f"[WARN] 删除旧备份失败 {backup.name}: {e}")


# ── Git 分支备份功能 ─────────────────────────────────────────


def _git_rel_path(filepath: str) -> str | None:
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
    path = Path(filepath)
    result = run_git("hash-object", str(path))
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def git_backup(filepath: str, max_backups: int, anchor: bool = False,
               dry_run: bool = False) -> bool:
    if dry_run:
        print(f"[DRY-RUN] 模拟 Git 备份: {filepath}")
        if anchor:
            print(f"[DRY-RUN]   标记为锚点备份")
        print(f"[DRY-RUN]   最大保留: {max_backups}")
        return True

    if not is_git_repo():
        print("[WARN] Git 仓库不可用，无法创建分支备份")
        return False

    path = Path(filepath)
    if not path.exists():
        print(f"[WARN] 文件不存在: {filepath}，跳过分支备份")
        return False

    head_check = run_git("rev-parse", "--verify", "HEAD")
    if head_check.returncode != 0:
        print("[WARN] 仓库尚无任何提交，请先执行 git commit 后再使用 Git 备份功能")
        print("[INFO] 将尝试文件复制备份作为替代...")
        return False

    rel_path = _git_rel_path(filepath)
    if rel_path is None:
        print(f"[WARN] 文件 {filepath} 不在仓库内")
        return False

    new_blob = _git_blob_hash(filepath)
    if new_blob:
        for branch in get_backup_branches():
            old_blob_result = run_git("rev-parse", f"{branch}:{rel_path}")
            if old_blob_result.returncode == 0:
                if old_blob_result.stdout.strip() == new_blob:
                    print(f"[INFO] {filepath} 与已有 Git 备份 {branch} 内容相同，跳过备份")
                    return True

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:18]
    anchor_tag = "-anchor" if anchor else ""
    backup_branch = f"{BACKUP_PREFIX}{timestamp}{anchor_tag}"

    blob_result = run_git("hash-object", "-w", str(path))
    if blob_result.returncode != 0:
        print(f"[WARN] hash-object 失败：{blob_result.stderr.strip()}")
        return False
    blob_hash = blob_result.stdout.strip()

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

    ref_result = run_git("update-ref", f"refs/heads/{backup_branch}", commit_sha)
    if ref_result.returncode != 0:
        print(f"[WARN] 创建备份分支失败：{ref_result.stderr.strip()}")
        return False

    print(f"[OK] 已创建 Git 备份分支：{backup_branch}")
    if anchor:
        print(f"[OK]   已标记为锚点备份")

    _auto_evict_old_git_backups(max_backups)
    return True


def _auto_evict_old_git_backups(max_backups: int) -> None:
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


# ── 备份入口 ───────────────────────────────────────────────


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


# ── 入口 ──────────────────────────────────────────────────


def main():
    anchor = False
    dry_run = False
    max_backups = None
    filepath = None

    args = sys.argv[1:]
    for arg in args:
        if arg in ("--anchor", "--keep"):
            anchor = True
        elif arg.startswith("--max-backups="):
            try:
                max_backups = int(arg.split("=", 1)[1])
            except ValueError:
                pass
        elif arg == "--dry-run":
            dry_run = True
        elif not arg.startswith("-"):
            filepath = arg

    if filepath is None:
        print("用法: python git_snapshot.py <文件路径> [--anchor] [--dry-run] [--max-backups=N]")
        sys.exit(1)

    cmd_snapshot(filepath, _resolve_max_backups(max_backups), anchor=anchor, dry_run=dry_run)


if __name__ == "__main__":
    main()
