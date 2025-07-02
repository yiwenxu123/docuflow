#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow PySide6 GUI 主程序
提供现代化的图形用户界面
"""

import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QListWidget, QComboBox, QLineEdit,
    QLabel, QFileDialog, QMessageBox, QTabWidget, QFormLayout,
    QProgressBar, QTextEdit
)
from PySide6.QtCore import QThread, QObject, Signal, Qt
from PySide6.QtGui import QFont

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from converter.document_converter import DocumentConverter
from exceptions import ConversionError

# 设置日志
logger = logging.getLogger(__name__)

class ConversionWorker(QObject):
    conversion_finished = Signal(str)
    conversion_error = Signal(str)

    def __init__(self, files_to_convert, output_dir, output_format):
        super().__init__()
        self.files_to_convert = files_to_convert
        # 空字符串转换为None，使用源文件所在目录
        self.output_dir = output_dir if output_dir.strip() else None
        self.output_format = output_format

    def run(self):
        try:
            converter = DocumentConverter()
            for file_path in self.files_to_convert:
                converter.convert_file(file_path, self.output_format, self.output_dir)
            self.conversion_finished.emit("所有文件转换成功！")
        except ConversionError as e:
            self.conversion_error.emit(str(e))
        except Exception as e:
            self.conversion_error.emit(f"发生意外错误: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.app.name} v{config.app.version}")
        self.setGeometry(100, 100, config.window.width, config.window.height)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧文件列表
        left_layout = QVBoxLayout()
        
        # 文件操作按钮
        file_buttons_layout = QHBoxLayout()
        self.add_files_button = QPushButton("添加文件")
        self.add_folder_button = QPushButton("添加文件夹")
        self.clear_files_button = QPushButton("清空列表")
        
        file_buttons_layout.addWidget(self.add_files_button)
        file_buttons_layout.addWidget(self.add_folder_button)
        file_buttons_layout.addWidget(self.clear_files_button)
        
        left_layout.addLayout(file_buttons_layout)
        
        # 文件列表
        self.file_list_widget = QListWidget()
        left_layout.addWidget(QLabel("待转换文件:"))
        left_layout.addWidget(self.file_list_widget)
        
        main_layout.addLayout(left_layout, 2)
        
        # 右侧设置和控制
        right_layout = QVBoxLayout()
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 设置选项卡
        settings_tab = QWidget()
        settings_layout = QFormLayout(settings_tab)
        
        # 输出目录设置
        default_dir = config.conversion.default_output_dir
        self.output_dir_edit = QLineEdit(str(default_dir) if default_dir else "")
        self.output_dir_edit.setPlaceholderText("留空则使用源文件所在目录")
        self.browse_button = QPushButton("浏览...")
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.browse_button)
        settings_layout.addRow("输出目录:", output_dir_layout)

        self.output_format_combo = QComboBox()
        for ext, fmt in config.files.supported_output_formats.items():
            self.output_format_combo.addItem(f"{fmt.description}", ext)
        settings_layout.addRow("输出格式:", self.output_format_combo)

        self.start_conversion_button = QPushButton("开始转换")
        self.start_conversion_button.setStyleSheet("font-size: 16px; padding: 10px;")

        right_layout.addWidget(tab_widget)
        right_layout.addWidget(self.start_conversion_button)
        
        tab_widget.addTab(settings_tab, "设置")
        
        # 日志选项卡
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        tab_widget.addTab(log_tab, "日志")
        
        main_layout.addLayout(right_layout, 1)
        
        # 连接信号
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.clear_files_button.clicked.connect(self.clear_files)
        self.browse_button.clicked.connect(self.browse_output_dir)
        self.start_conversion_button.clicked.connect(self.start_conversion)
        
        logger.info(f"{config.app.name} v{config.app.version} 已启动")

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", 
            config.get_file_dialog_filter('input')
        )
        for file_path in files:
            if not self.file_list_widget.findItems(file_path, Qt.MatchExactly):
                self.file_list_widget.addItem(file_path)
                logger.info(f"已添加文件: {file_path}")

    def start_conversion(self):
        files_to_convert = [self.file_list_widget.item(i).text() for i in range(self.file_list_widget.count())]
        if not files_to_convert:
            QMessageBox.warning(self, "没有文件", "请先添加要转换的文件。")
            return

        output_dir = self.output_dir_edit.text()
        output_format = self.output_format_combo.currentData()

        self.start_conversion_button.setEnabled(False)
        logger.info(f"开始转换 {len(files_to_convert)} 个文件到 {output_format} 格式...")

        self.thread = QThread()
        self.worker = ConversionWorker(files_to_convert, output_dir, output_format)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.conversion_finished.connect(self.on_conversion_finished)
        self.worker.conversion_error.connect(self.on_conversion_error)

        self.thread.start()

    def on_conversion_finished(self, message):
        QMessageBox.information(self, "转换完成", message)
        logger.info(message)
        self.thread.quit()
        self.thread.wait()
        self.start_conversion_button.setEnabled(True)

    def on_conversion_error(self, error_message):
        QMessageBox.critical(self, "转换失败", error_message)
        logger.error(error_message)
        self.thread.quit()
        self.thread.wait()
        self.start_conversion_button.setEnabled(True)

    def add_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if directory:
            folder_path = Path(directory)
            for extension in config.files.all_input_extensions:
                for file_path in folder_path.rglob(f"*{extension}"):
                    if file_path.is_file():
                        if not self.file_list_widget.findItems(str(file_path), Qt.MatchExactly):
                            self.file_list_widget.addItem(str(file_path))
                            logger.info(f"已添加文件: {file_path}")

    def clear_files(self):
        self.file_list_widget.clear()
        logger.info("已清空文件列表")

    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir_edit.setText(directory)

def setup_qt_plugins():
    """设置Qt插件路径"""
    import PySide6
    plugin_path = Path(PySide6.__file__).parent / "Qt" / "plugins"
    if plugin_path.exists():
        os.environ['QT_PLUGIN_PATH'] = str(plugin_path)
        print(f"设置Qt插件路径: {plugin_path}")
        
        # 检查cocoa插件
        cocoa_plugin = plugin_path / "platforms" / "libqcocoa.dylib"
        if cocoa_plugin.exists():
            print(f"找到cocoa插件: {cocoa_plugin}")
        else:
            print(f"警告: 未找到cocoa插件: {cocoa_plugin}")

def main():
    """主函数"""
    # 设置Qt插件
    setup_qt_plugins()
    
    print(f"启动 {config.app.name} v{config.app.version}...")
    
    app = QApplication(sys.argv)
    app.setApplicationName(config.app.name)
    app.setApplicationVersion(config.app.version)
    
    # 设置应用字体
    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())