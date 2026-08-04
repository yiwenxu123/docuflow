#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow 交互式 CLI 入口（兼容层）

交互功能已并入 cli.py（cli.py -i 或直接运行 cli.py），
本文件仅为保持旧入口兼容的薄壳。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli import interactive_mode  # noqa: E402


def main():
    return interactive_mode()


if __name__ == "__main__":
    sys.exit(main())
