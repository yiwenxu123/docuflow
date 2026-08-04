#!/usr/bin/env python3
import sys
import logging
from pathlib import Path
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QPushButton, QListWidget, QFileDialog, QTextEdit, QProgressBar, 
        QMessageBox, QSplitter, QTabWidget, QGroupBox, QFormLayout, 
        QLineEdit, QComboBox, QLabel, QDialog, QDialogButtonBox
    )
    from PySide6.QtCore import Qt, Signal, QObject, QThread
    from PySide6.QtGui import QDropEvent
except ImportError:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QPushButton, QListWidget, QFileDialog, QTextEdit, QProgressBar, 
        QMessageBox, QSplitter, QTabWidget, QGroupBox, QFormLayout, 
        QLineEdit, QComboBox, QLabel, QDialog, QDialogButtonBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal as Signal, QObject, QThread
    from PyQt5.QtGui import QDropEvent

from converter.document_converter import DocumentConverter, ConversionError
from config import config

# 日志记录器
logger = logging.getLogger(__name__)

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.widget = QTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        # 直接添加到widget，避免信号槽问题
        self.widget.append(msg)

class ConversionWorker(QObject):
    conversion_finished = Signal(str)
    conversion_error = Signal(str)
    conversion_completed = Signal(dict)  # 新增：传递完整的转换结果

    def __init__(self, files_to_convert, output_dir, output_format):
        super().__init__()
        self.files_to_convert = files_to_convert
        # 空字符串转换为None，使用源文件所在目录
        self.output_dir = output_dir if output_dir.strip() else None
        self.output_format = output_format

    def run(self):
        converter = DocumentConverter()
        results = {
            'successful': [],
            'failed': [],
            'errors': []
        }
        
        for file_path in self.files_to_convert:
            try:
                output_file = converter.convert_file(file_path, self.output_format, self.output_dir)
                if output_file:
                    results['successful'].append({
                        'input_file': file_path,
                        'output_file': output_file
                    })
                else:
                    results['failed'].append(file_path)
                    results['errors'].append(f"{Path(file_path).name}: 转换失败")
            except ConversionError as e:
                results['failed'].append(file_path)
                results['errors'].append(f"{Path(file_path).name}: {str(e)}")
            except Exception as e:
                results['failed'].append(file_path)
                results['errors'].append(f"{Path(file_path).name}: 发生意外错误: {str(e)}")
        
        # 只发出完整的转换结果信号，避免重复通知
        self.conversion_completed.emit(results)
        
        # 仅在完全成功或完全失败时发出旧信号，但不再用于UI通知
        if len(results['failed']) == 0:
            self.conversion_finished.emit("所有文件转换成功！")
        elif len(results['successful']) == 0:
            self.conversion_error.emit("所有文件转换失败")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.window.title)
        self.setGeometry(100, 100, config.window.width, config.window.height)
        self.setMinimumSize(config.window.min_width, config.window.min_height)
        self.setAcceptDrops(True)

        self._init_ui()
        self._setup_logging()

    def _init_ui(self):
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧面板：文件列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.ExtendedSelection)

        button_layout = QHBoxLayout()
        self.add_files_button = QPushButton("添加文件")
        self.add_folder_button = QPushButton("添加文件夹")
        self.remove_files_button = QPushButton("移除选中")
        self.clear_files_button = QPushButton("清空列表")
        button_layout.addWidget(self.add_files_button)
        button_layout.addWidget(self.add_folder_button)
        button_layout.addWidget(self.remove_files_button)
        button_layout.addWidget(self.clear_files_button)

        left_layout.addWidget(QLabel("待转换文件列表："))
        left_layout.addWidget(self.file_list_widget)
        left_layout.addLayout(button_layout)
        
        splitter.addWidget(left_panel)

        # 右侧面板：设置和日志
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
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
        
        tab_widget.addTab(settings_tab, "转换设置")

        # 日志选项卡
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_widget_handler = QTextEditLogger(self)
        log_layout.addWidget(self.log_widget_handler.widget)
        tab_widget.addTab(log_tab, "运行日志")

        splitter.addWidget(right_panel)
        splitter.setSizes([self.width() // 2, self.width() // 2])

        # 连接信号和槽
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.remove_files_button.clicked.connect(self.remove_files)
        self.clear_files_button.clicked.connect(self.clear_files)
        self.browse_button.clicked.connect(self.browse_output_dir)
        self.start_conversion_button.clicked.connect(self.start_conversion)

    def _setup_logging(self):
        # 清除现有的处理器，避免重复
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置基本配置
        logging.basicConfig(
            level=config.logging.level,
            format=config.logging.format,
            handlers=[
                logging.FileHandler(config.logging.file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # 添加GUI日志处理器
        log_formatter = logging.Formatter(config.logging.format)
        self.log_widget_handler.setFormatter(log_formatter)
        root_logger.addHandler(self.log_widget_handler)
        
        # 设置第三方库日志级别
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('pdfplumber').setLevel(logging.WARNING)
        
        logger.info(f"{config.app.name} v{config.app.version} 已启动")

    def add_files(self):
        """添加单个或多个文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "",
            "All Files (*)"
        )
        for file_path in files:
            if file_path and file_path not in [self.file_list_widget.item(i).text() 
                                             for i in range(self.file_list_widget.count())]:
                self.file_list_widget.addItem(file_path)

    def add_folder(self):
        """添加文件夹中的所有文件"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            from pathlib import Path
            folder_path = Path(folder)
            files_added = 0
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    file_str = str(file_path)
                    if file_str not in [self.file_list_widget.item(i).text() 
                                      for i in range(self.file_list_widget.count())]:
                        self.file_list_widget.addItem(file_str)
                        files_added += 1
            
            if files_added > 0:
                QMessageBox.information(self, "成功", f"已添加 {files_added} 个文件")

    def remove_files(self):
        """移除选中的文件"""
        for item in self.file_list_widget.selectedItems():
            self.file_list_widget.takeItem(self.file_list_widget.row(item))

    def clear_files(self):
        """清空文件列表"""
        self.file_list_widget.clear()

    def browse_output_dir(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir_edit.setText(directory)

    def start_conversion(self):
        """开始转换"""
        if self.file_list_widget.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加需要转换的文件！")
            return

        # 收集所有文件
        files_to_convert = []
        for i in range(self.file_list_widget.count()):
            files_to_convert.append(self.file_list_widget.item(i).text())

        output_dir = self.output_dir_edit.text()
        output_format = self.output_format_combo.currentData()

        # 禁用转换按钮
        self.start_conversion_button.setEnabled(False)
        self.start_conversion_button.setText("转换中...")

        # 创建转换线程
        self.worker = ConversionWorker(files_to_convert, output_dir, output_format)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # 连接信号
        self.worker.conversion_error.connect(self.on_conversion_error)
        self.worker.conversion_completed.connect(self.on_conversion_completed)
        # 注意：conversion_finished信号已废弃，只使用conversion_completed信号

        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_conversion_completed(self, results):
        """转换完成处理"""
        self.thread.quit()
        self.thread.wait()
        
        successful_count = len(results['successful'])
        failed_count = len(results['failed'])
        
        # 启用转换按钮
        self.start_conversion_button.setEnabled(True)
        self.start_conversion_button.setText("开始转换")
        
        if failed_count == 0:
            QMessageBox.information(self, "成功", f"所有 {successful_count} 个文件转换成功！")
        elif successful_count == 0:
            QMessageBox.critical(self, "失败", f"所有 {failed_count} 个文件转换失败")
        else:
            QMessageBox.warning(self, "部分成功", 
                              f"成功转换 {successful_count} 个文件，\n"
                              f"失败 {failed_count} 个文件")
        
        # 显示详细错误信息
        if results['errors']:
            logger.error("转换错误详情：")
            for error in results['errors']:
                logger.error(error)

    def on_conversion_finished(self, message):
        """转换成功 - 已废弃，避免重复通知"""
        # 这个方法已被废弃，通知由on_conversion_completed统一处理
        pass

    def on_conversion_error(self, message):
        """转换失败"""
        self.thread.quit()
        self.thread.wait()
        
        # 启用转换按钮
        self.start_conversion_button.setEnabled(True)
        self.start_conversion_button.setText("开始转换")
        
        QMessageBox.critical(self, "错误", message)

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if Path(file_path).is_file():
                files.append(file_path)
            elif Path(file_path).is_dir():
                # 如果是文件夹，添加所有文件
                from pathlib import Path as pathlib_Path
                folder_path = pathlib_Path(file_path)
                for file_path in folder_path.rglob('*'):
                    if file_path.is_file():
                        files.append(str(file_path))
        
        # 添加文件到列表
        for file_path in files:
            if file_path not in [self.file_list_widget.item(i).text() 
                               for i in range(self.file_list_widget.count())]:
                self.file_list_widget.addItem(file_path)

class FileTypeFilterDialog(QDialog):
    """文件类型过滤对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择文件类型")
        self.setModal(True)
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems([
            "所有文件 (*.*)",
            "PDF文件 (*.pdf)",
            "Word文件 (*.docx)",
            "Excel文件 (*.xlsx)",
            "图片文件 (*.jpg *.png)",
            "文本文件 (*.txt)",
            "Markdown文件 (*.md)"
        ])
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(QLabel("选择文件类型："))
        layout.addWidget(self.file_type_combo)
        layout.addWidget(buttons)
    
    def get_selected_filter(self):
        """获取选择的文件过滤器"""
        return self.file_type_combo.currentText()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())