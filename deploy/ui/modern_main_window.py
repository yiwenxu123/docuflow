#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 现代化主窗口界面
优化版本，包含更好的样式和用户体验
"""

# 简化导入，只保留必要部分
import os
import sys
from pathlib import Path
try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QComboBox, QLineEdit, QProgressBar,
        QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
        QDialog, QDialogButtonBox, QApplication
    )
    from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal
    from PySide6.QtGui import QFont, QColor, QLinearGradient
    QT_VERSION = "PySide6"
except ImportError:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QComboBox, QLineEdit, QProgressBar,
        QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
        QDialog, QDialogButtonBox, QApplication
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QFont, QColor, QLinearGradient
    QT_VERSION = "PyQt5"

from .converter.document_converter import DocumentConverter
from .utils.file_utils import get_supported_formats, is_supported_file

class ModernButton(QPushButton):
    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setup_style()

    def setup_style(self):
        # 简化样式，减少渐变，使用纯色以使界面更简洁
        if self.button_type == "primary":
            style = """
                QPushButton { background-color: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; font-size: 14px; }
                QPushButton:hover { background-color: #45a049; }
            """
        elif self.button_type == "secondary":
            style = """
                QPushButton { background-color: #f0f0f0; color: #333; border: 1px solid #ccc; padding: 8px 16px; border-radius: 5px; font-size: 13px; }
                QPushButton:hover { background-color: #e0e0e0; }
            """
        self.setStyleSheet(style)

class ModernFileItem(QWidget):
    # 简化文件项，移除不必要细节
    def __init__(self, file_path, parent_window):
        super().__init__()
        self.file_path = file_path
        self.parent_window = parent_window
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        name_label = QLabel(Path(self.file_path).name)
        layout.addWidget(name_label)
        layout.addStretch()
        delete_btn = QPushButton("X")
        delete_btn.clicked.connect(self.delete_file)
        layout.addWidget(delete_btn)
        self.setStyleSheet("background-color: #f9f9f9; border-bottom: 1px solid #eee;")

    def delete_file(self):
        self.parent_window.remove_file(self.file_path)

class ConversionWorker(QThread):
    """转换工作线程"""
    progress_updated = pyqtSignal(int, str)
    file_processed = pyqtSignal(str, bool, str)
    conversion_finished = pyqtSignal(list)
    
    def __init__(self, files, output_format, output_dir, keep_original_name):
        super().__init__()
        self.files = files
        self.output_format = output_format
        self.output_dir = output_dir
        self.keep_original_name = keep_original_name
        self.converter = DocumentConverter()
        
    def run(self):
        """执行转换任务"""
        total_files = len(self.files)
        converted_files = []
        
        for i, file_path in enumerate(self.files):
            try:
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, f"正在转换: {Path(file_path).name}")
                
                output_file = self.converter.convert_file(
                    file_path, self.output_format, self.output_dir, self.keep_original_name
                )
                
                if output_file:
                    converted_files.append(output_file)
                    self.file_processed.emit(Path(file_path).name, True, "")
                else:
                    self.file_processed.emit(Path(file_path).name, False, "转换失败")
                    
            except Exception as e:
                self.file_processed.emit(Path(file_path).name, False, str(e))
        
        self.progress_updated.emit(100, "转换完成")
        self.conversion_finished.emit(converted_files)

class ModernMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DocuFlow - 简洁文档转换")
        self.resize(800, 600)
        self.selected_files = []
        self.converter = DocumentConverter()
        self.conversion_worker = None
        self.setup_ui()

    def setup_ui(self):
        # 简化布局：左侧文件列表，右侧设置和转换按钮
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 文件列表
        left_layout = QVBoxLayout()
        self.file_list = QListWidget()
        left_layout.addWidget(QLabel("文件列表"))
        left_layout.addWidget(self.file_list)
        
        # 文件操作按钮
        file_btn_layout = QHBoxLayout()
        add_btn = ModernButton("添加文件")
        add_btn.clicked.connect(self.add_files)
        clear_btn = ModernButton("清空列表", "secondary")
        clear_btn.clicked.connect(self.clear_files)
        file_btn_layout.addWidget(add_btn)
        file_btn_layout.addWidget(clear_btn)
        left_layout.addLayout(file_btn_layout)
        
        main_layout.addLayout(left_layout)

        # 设置面板
        right_layout = QVBoxLayout()
        
        # 输出格式选择
        right_layout.addWidget(QLabel("输出格式"))
        self.output_format = QComboBox()
        self.output_format.addItems([".md", ".pdf", ".docx", ".html", ".txt"])
        right_layout.addWidget(self.output_format)
        
        # 输出目录选择
        right_layout.addWidget(QLabel("输出目录"))
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录（留空使用源文件目录）")
        browse_btn = ModernButton("浏览", "secondary")
        browse_btn.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(browse_btn)
        right_layout.addLayout(output_dir_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        right_layout.addWidget(self.status_label)
        
        # 转换按钮
        self.convert_btn = ModernButton("开始转换", "primary")
        self.convert_btn.clicked.connect(self.start_conversion)
        right_layout.addWidget(self.convert_btn)
        
        right_layout.addStretch()
        main_layout.addLayout(right_layout)

    def add_files(self):
        # 改进文件选择：允许浏览整个电脑
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "/", "All Files (*)")
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                item = QListWidgetItem()
                widget = ModernFileItem(file, self)
                item.setSizeHint(widget.sizeHint())
                self.file_list.addItem(item)
                self.file_list.setItemWidget(item, widget)

    def clear_files(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.file_list.clear()
        self.status_label.setText("就绪")

    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def remove_file(self, file_path):
        self.selected_files.remove(file_path)
        # 刷新列表
        self.file_list.clear()
        for f in self.selected_files:
            item = QListWidgetItem()
            widget = ModernFileItem(f, self)
            item.setSizeHint(widget.sizeHint())
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, widget)

    def start_conversion(self):
        """开始转换"""
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return

        output_format = self.output_format.currentText()
        output_dir = self.output_dir_edit.text().strip() or None

        # 禁用转换按钮，显示进度条
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("准备转换...")

        # 创建并启动转换工作线程
        self.conversion_worker = ConversionWorker(
            self.selected_files, output_format, output_dir, True
        )
        self.conversion_worker.progress_updated.connect(self.update_progress)
        self.conversion_worker.file_processed.connect(self.file_processed)
        self.conversion_worker.conversion_finished.connect(self.conversion_finished)
        self.conversion_worker.start()

    def update_progress(self, value, message):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def file_processed(self, filename, success, error_msg):
        """处理单个文件完成"""
        if success:
            self.status_label.setText(f"✓ {filename} 转换成功")
        else:
            self.status_label.setText(f"✗ {filename} 转换失败: {error_msg}")

    def conversion_finished(self, converted_files):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if converted_files:
            QMessageBox.information(
                self, "转换完成", 
                f"成功转换 {len(converted_files)} 个文件！\n\n"
                f"输出文件:\n" + "\n".join([Path(f).name for f in converted_files[:5]]) +
                (f"\n... 还有 {len(converted_files) - 5} 个文件" if len(converted_files) > 5 else "")
            )
            self.status_label.setText(f"转换完成，共 {len(converted_files)} 个文件")
        else:
            QMessageBox.warning(self, "转换失败", "没有文件转换成功，请检查文件格式和错误信息")
            self.status_label.setText("转换失败")

def main():
    app = QApplication(sys.argv)
    window = ModernMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()