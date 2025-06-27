#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow - 主窗口界面
"""

import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
    QCheckBox, QSplitter, QFrame, QDialog, QDialogButtonBox, QStyledItemDelegate
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QFontMetrics

class ComboBoxDelegate(QStyledItemDelegate):
    """自定义下拉菜单委托，用于显示选中项的对号"""
    
    def __init__(self, combo_box, parent=None):
        super().__init__(parent)
        self.combo_box = combo_box
    
    def paint(self, painter, option, index):
        # 调用父类的绘制方法
        super().paint(painter, option, index)
        
        # 如果是当前选中的项，绘制对号
        if index.row() == self.combo_box.currentIndex():
            painter.save()
            
            # 设置对号的颜色和字体
            painter.setPen(Qt.green)
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            
            # 计算对号的位置
            check_mark = "✓"
            fm = QFontMetrics(font)
            check_width = fm.width(check_mark)
            check_height = fm.height()
            
            x = option.rect.left() + 12
            y = option.rect.top() + (option.rect.height() + check_height) // 2 - 2
            
            # 绘制对号
            painter.drawText(x, y, check_mark)
            painter.restore()

class FileTypeFilterDialog(QDialog):
    """文件类型过滤对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择要转换的文件类型")
        self.setModal(True)
        self.resize(300, 250)
        self.selected_types = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel("请选择要转换的文件类型：")
        layout.addWidget(info_label)
        
        # 文件类型复选框
        self.checkboxes = {}
        file_types = {
            '.docx': 'Word文档 (.docx)',
            '.md': 'Markdown (.md)',
            '.pdf': 'PDF文档 (.pdf)',
            '.html': 'HTML文件 (.html)',
            '.epub': 'EPUB电子书 (.epub)'
        }
        
        for ext, desc in file_types.items():
            checkbox = QCheckBox(desc)
            checkbox.setChecked(True)  # 默认全选
            self.checkboxes[ext] = checkbox
            layout.addWidget(checkbox)
        
        # 全选/全不选按钮
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_none_btn = QPushButton("全不选")
        select_all_btn.clicked.connect(self.select_all)
        select_none_btn.clicked.connect(self.select_none)
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(select_none_btn)
        layout.addLayout(button_layout)
        
        # 对话框按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def select_all(self):
        """全选"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
    
    def select_none(self):
        """全不选"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
    
    def get_selected_types(self):
        """获取选中的文件类型"""
        return [ext for ext, checkbox in self.checkboxes.items() if checkbox.isChecked()]

class FileListItem(QWidget):
    """自定义文件列表项，包含删除按钮"""
    
    def __init__(self, file_path, parent_window):
        super().__init__()
        self.file_path = file_path
        self.parent_window = parent_window
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)  # 减少垂直边距
        layout.setSpacing(8)  # 减少间距
        
        # 设置固定高度使列表更紧凑
        self.setFixedHeight(32)
        
        # 文件图标和名称
        file_label = QLabel(f"📄 {os.path.basename(self.file_path)}")
        file_label.setToolTip(self.file_path)
        file_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 13px;
                padding: 2px;
            }
        """)
        layout.addWidget(file_label)
        
        layout.addStretch()
        
        # 删除按钮 - 简洁的叉号设计
        delete_btn = QPushButton("❌")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                font-size: 12px;
                text-align: center;
            }
            QPushButton:hover {
                color: #ff4444;
                font-size: 14px;
            }
            QPushButton:pressed {
                color: #cc0000;
            }
        """)
        delete_btn.setToolTip("删除此文件")
        delete_btn.clicked.connect(self.delete_file)
        layout.addWidget(delete_btn)
    
    def delete_file(self):
        """删除文件"""
        self.parent_window.remove_file(self.file_path)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QDragEnterEvent, QDropEvent
from converter.document_converter import DocumentConverter
from utils.file_utils import get_supported_formats, is_supported_file

class ConversionWorker(QThread):
    """转换工作线程"""
    progress_updated = pyqtSignal(int, str)  # 进度, 状态信息
    file_processed = pyqtSignal(str, bool, str)  # 文件名, 是否成功, 错误信息
    conversion_finished = pyqtSignal(list)  # 转换完成的文件列表
    
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
                # 更新进度
                progress = int((i / total_files) * 100)
                self.progress_updated.emit(progress, f"正在转换: {os.path.basename(file_path)}")
                
                # 执行转换
                output_file = self.converter.convert_file(
                    file_path, self.output_format, self.output_dir, self.keep_original_name
                )
                
                if output_file:
                    converted_files.append(output_file)
                    self.file_processed.emit(os.path.basename(file_path), True, "")
                else:
                    self.file_processed.emit(os.path.basename(file_path), False, "转换失败")
                    
            except Exception as e:
                self.file_processed.emit(os.path.basename(file_path), False, str(e))
        
        # 转换完成
        self.progress_updated.emit(100, "转换完成")
        self.conversion_finished.emit(converted_files)

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.conversion_worker = None
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DocuFlow - 文档转换器")
        self.setGeometry(100, 100, 900, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("📄 DocuFlow 文档转换器")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 文件选择区域
        file_group = self.create_file_selection_group()
        main_layout.addWidget(file_group)
        
        # 转换设置区域
        settings_group = self.create_conversion_settings_group()
        main_layout.addWidget(settings_group)
        
        # 进度和状态区域
        progress_group = self.create_progress_group()
        main_layout.addWidget(progress_group)
        
        # 转换按钮
        self.convert_button = QPushButton("🚀 开始转换")
        self.convert_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.convert_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        main_layout.addWidget(self.convert_button)
        
        # 设置拖拽支持
        self.setAcceptDrops(True)
        
    def create_file_selection_group(self):
        """创建文件选择组"""
        group = QGroupBox("📁 文件选择")
        layout = QVBoxLayout(group)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.select_files_btn = QPushButton("选择文件")
        self.select_folder_btn = QPushButton("选择文件夹")
        self.clear_files_btn = QPushButton("清空列表")
        
        for btn in [self.select_files_btn, self.select_folder_btn, self.clear_files_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d5dbdb;
                }
            """)
        
        button_layout.addWidget(self.select_files_btn)
        button_layout.addWidget(self.select_folder_btn)
        button_layout.addWidget(self.clear_files_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(200)  # 增加最小高度
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                padding: 5px;
            }
            QListWidget::item {
                padding: 3px 5px;
                margin: 1px 0px;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f0f8f0;
            }
            QListWidget::item:selected {
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
            }
        """)
        self.file_list.setAlternatingRowColors(False)  # 关闭交替颜色，使用自定义样式
        layout.addWidget(self.file_list)
        
        # 拖拽提示
        drag_label = QLabel("💡 提示: 您也可以直接拖拽文件到此窗口")
        drag_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        drag_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(drag_label)
        
        # 连接信号
        self.select_files_btn.clicked.connect(self.select_files)
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.clear_files_btn.clicked.connect(self.clear_files)
        
        return group
        
    def create_conversion_settings_group(self):
        """创建转换设置组"""
        group = QGroupBox("⚙️ 转换设置")
        layout = QGridLayout(group)
        
        # 输出格式
        layout.addWidget(QLabel("输出格式:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Word文档 (.docx)",
            "Markdown (.md)", 
            "PDF文档 (.pdf)",
            "HTML文件 (.html)",
            "EPUB电子书 (.epub)"
        ])
        
        # 设置自定义委托来显示对号
        delegate = ComboBoxDelegate(self.format_combo)
        self.format_combo.setItemDelegate(delegate)
        
        # 优化的下拉菜单样式
        format_combo_style = """
            QComboBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #4CAF50;
            }
            QComboBox:focus {
                border-color: #4CAF50;
                outline: none;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #e0e0e0;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #f8f9fa;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 8px solid #666;
                width: 0;
                height: 0;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                outline: none;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 10px 12px 10px 35px;
                border: none;
                min-height: 25px;
                background-color: transparent;
                color: #333;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f0f8f0;
                color: #2e7d32;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: transparent;
                color: #2e7d32;
            }
        """
        self.format_combo.setStyleSheet(format_combo_style)
        layout.addWidget(self.format_combo, 0, 1)
        
        # 输出目录
        layout.addWidget(QLabel("输出目录:"), 1, 0)
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("默认与原文件相同目录")
        self.output_dir_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.browse_output_btn)
        layout.addLayout(output_layout, 1, 1)
        
        # 文件命名选项
        self.keep_name_checkbox = QCheckBox("保留原文件名（否则添加格式后缀）")
        self.keep_name_checkbox.setChecked(True)
        layout.addWidget(self.keep_name_checkbox, 2, 0, 1, 2)
        
        # 连接信号
        self.browse_output_btn.clicked.connect(self.browse_output_directory)
        
        return group
        
    def create_progress_group(self):
        """创建进度显示组"""
        group = QGroupBox("📊 转换进度")
        layout = QVBoxLayout(group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 结果文本框
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(120)
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.result_text)
        
        return group
    
    def select_files(self):
        """选择文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择要转换的文件", "",
            "支持的文件 (*.docx *.md *.pdf *.html *.epub);;Word文档 (*.docx);;Markdown (*.md);;PDF (*.pdf);;HTML (*.html);;EPUB (*.epub);;所有文件 (*)"
        )
        if files:
            self.add_files(files)
    
    def select_folder(self):
        """选择文件夹并添加其中的文件"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择文件夹", "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder_path:
            # 显示文件类型过滤对话框
            filter_dialog = FileTypeFilterDialog(self)
            if filter_dialog.exec_() == QDialog.Accepted:
                selected_types = filter_dialog.get_selected_types()
                
                if not selected_types:
                    QMessageBox.information(self, "提示", "请至少选择一种文件类型。")
                    return
                
                files = []
                for root, dirs, filenames in os.walk(folder_path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        # 检查文件是否为支持的格式且在选中的类型中
                        if is_supported_file(file_path):
                            file_ext = os.path.splitext(filename)[1].lower()
                            if file_ext in selected_types:
                                files.append(file_path)
                
                if files:
                    self.add_files(files)
                    QMessageBox.information(self, "成功", f"已添加 {len(files)} 个文件到转换列表。")
                else:
                    QMessageBox.information(self, "提示", "所选文件夹中没有找到符合条件的文件。")
    
    def add_files(self, files):
        """添加文件到列表"""
        for file_path in files:
            if file_path not in self.selected_files and is_supported_file(file_path):
                self.selected_files.append(file_path)
                
                # 创建自定义列表项
                item = QListWidgetItem()
                file_widget = FileListItem(file_path, self)
                # 设置列表项的固定高度
                item.setSizeHint(file_widget.size())
                
                self.file_list.addItem(item)
                self.file_list.setItemWidget(item, file_widget)
        
        self.update_ui_state()
    
    def remove_file(self, file_path):
        """从列表中移除指定文件"""
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            
            # 找到并移除对应的列表项
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                widget = self.file_list.itemWidget(item)
                if widget and widget.file_path == file_path:
                    self.file_list.takeItem(i)
                    break
            
            self.update_ui_state()
    
    def clear_files(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.file_list.clear()
        self.update_ui_state()
    
    def browse_output_directory(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir_edit.setText(directory)
    
    def update_ui_state(self):
        """更新UI状态"""
        has_files = len(self.selected_files) > 0
        self.convert_button.setEnabled(has_files)
        
        if has_files:
            self.status_label.setText(f"已选择 {len(self.selected_files)} 个文件")
        else:
            self.status_label.setText("请选择要转换的文件")
    
    def start_conversion(self):
        """开始转换"""
        if not self.selected_files:
            QMessageBox.warning(self, "警告", "请先选择要转换的文件")
            return
        
        # 获取转换参数
        format_text = self.format_combo.currentText()
        output_format = format_text.split('(')[1].split(')')[0]  # 提取格式如 .pdf
        output_dir = self.output_dir_edit.text().strip() or None
        keep_original_name = self.keep_name_checkbox.isChecked()
        
        # 禁用转换按钮
        self.convert_button.setEnabled(False)
        self.convert_button.setText("转换中...")
        
        # 清空结果文本
        self.result_text.clear()
        
        # 创建并启动工作线程
        self.conversion_worker = ConversionWorker(
            self.selected_files, output_format, output_dir, keep_original_name
        )
        self.conversion_worker.progress_updated.connect(self.update_progress)
        self.conversion_worker.file_processed.connect(self.file_processed)
        self.conversion_worker.conversion_finished.connect(self.conversion_finished)
        self.conversion_worker.start()
    
    def update_progress(self, progress, status):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def file_processed(self, filename, success, error_msg):
        """文件处理完成"""
        if success:
            self.result_text.append(f"✅ {filename} - 转换成功")
        else:
            self.result_text.append(f"❌ {filename} - 转换失败: {error_msg}")
    
    def conversion_finished(self, converted_files):
        """转换完成"""
        self.convert_button.setEnabled(True)
        self.convert_button.setText("🚀 开始转换")
        
        if converted_files:
            # 显示完成对话框
            msg = QMessageBox()
            msg.setWindowTitle("转换完成")
            msg.setText(f"成功转换了 {len(converted_files)} 个文件！")
            msg.setInformativeText("是否打开输出文件夹？")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            if msg.exec_() == QMessageBox.Yes:
                # 打开输出文件夹
                output_dir = os.path.dirname(converted_files[0])
                os.system(f'open "{output_dir}"')  # macOS
        else:
            QMessageBox.warning(self, "转换失败", "没有文件转换成功，请检查文件格式和错误信息。")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path) and is_supported_file(file_path):
                files.append(file_path)
            elif os.path.isdir(file_path):
                # 处理文件夹
                for root, dirs, filenames in os.walk(file_path):
                    for filename in filenames:
                        full_path = os.path.join(root, filename)
                        if is_supported_file(full_path):
                            files.append(full_path)
        
        if files:
            self.add_files(files)
        else:
            QMessageBox.information(self, "提示", "拖拽的文件中没有支持的文档格式")