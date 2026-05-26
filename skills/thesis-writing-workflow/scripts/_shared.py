# -*- coding: utf-8 -*-
"""git_snapshot 的 Windows UTF-8 兼容工具（workflow 专用精简版）。

humanizer 和 format-cleaner 的 _shared.py 含各自 checker 所需的其他函数，
本文件仅含 git_snapshot.py 所需的 setup_windows_utf8。
"""

import io
import os
import sys


def setup_windows_utf8() -> None:
    """强制 stdout/stderr 使用 UTF-8（Windows GBK 终端兼容）。

    在 pytest、IDE 控制台等非标准输出环境下静默回退。
    """
    if os.name != "nt":
        return
    for attr in ("stdout", "stderr"):
        stream = getattr(sys, attr)
        try:
            setattr(sys, attr, io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace"))
        except (AttributeError, ValueError):
            pass
