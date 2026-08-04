#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow GUI 入口（兼容层）

实际实现在 ui/main_window.py，本文件仅为保持旧入口兼容的薄壳。
启动器与旧脚本仍可引用 main_pyside.py。
"""

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    gui = MainWindow()
    gui.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
