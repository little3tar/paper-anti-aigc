"""hooks 共享工具模块 — Windows UTF-8 终端兼容。

session-start 和 pre-tool-use 钩子共用此模块，避免两处独立实现。
"""
import sys
import io
import os


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
