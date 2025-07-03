#!/usr/bin/env python3
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QFileDialog, QTextEdit, QProgressBar, 
    QMessageBox, QSplitter, QTabWidget, QGroupBox, QFormLayout, 
    QLineEdit, QComboBox, QLabel
)
from PySide6.QtCore import Qt, Signal, QObject, QThread
from converter.document_converter import DocumentConverter, ConversionError
from PySide6.QtGui import QDropEvent

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

class DocuFlowGUI(QMainWindow):
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

    def add_files(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(config.get_file_dialog_filter())
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            for file in files:
                if not self.file_list_widget.findItems(file, Qt.MatchExactly):
                    self.file_list_widget.addItem(file)
                    logger.info(f"已添加文件: {file}")

    def remove_files(self):
        for item in self.file_list_widget.selectedItems():
            self.file_list_widget.takeItem(self.file_list_widget.row(item))
            logger.info(f"已移除文件: {item.text()}")

    def clear_files(self):
        self.file_list_widget.clear()
        logger.info("文件列表已清空")

    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir_edit.setText(directory)
            logger.info(f"输出目录已更改为: {directory}")

    def dragEnterEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if Path(file_path).is_file():
                if not self.file_list_widget.findItems(file_path, Qt.MatchExactly):
                    self.file_list_widget.addItem(file_path)
                    logger.info(f"已通过拖放添加文件: {file_path}")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '退出',
                                     "确定要退出吗?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)
    gui = DocuFlowGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()