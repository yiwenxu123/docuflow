#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DocuFlow GUI：选择文件、转换并投递到 Obsidian 收件箱"""

import logging
import sys
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QListWidget,
        QFileDialog,
        QTextEdit,
        QProgressBar,
        QMessageBox,
        QSplitter,
        QTabWidget,
        QFormLayout,
        QLineEdit,
        QComboBox,
        QLabel,
        QCheckBox,
    )
    from PySide6.QtCore import Qt, Signal, QObject, QThread, QUrl
    from PySide6.QtGui import QDropEvent, QDesktopServices
except ImportError:
    from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QListWidget,
        QFileDialog,
        QTextEdit,
        QProgressBar,
        QMessageBox,
        QSplitter,
        QTabWidget,
        QFormLayout,
        QLineEdit,
        QComboBox,
        QLabel,
        QCheckBox,
    )
    from PyQt5.QtCore import Qt, pyqtSignal as Signal, QObject, QThread, QUrl
    from PyQt5.QtGui import QDropEvent, QDesktopServices

from config import config
from converter.kb_pipeline import default_vault_dest, detect_obsidian_vault
from utils.file_utils import is_supported_file

logger = logging.getLogger(__name__)


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        self.widget.append(self.format(record))


class IngestWorker(QObject):
    """后台转换并投递"""

    finished = Signal(dict)
    failed = Signal(str)

    def __init__(
        self, files, vault_dir, dest_subdir, use_markitdown, ocr_mode, pdf_engine
    ):
        super().__init__()
        self.files = files
        self.vault_dir = vault_dir
        self.dest_subdir = dest_subdir
        self.use_markitdown = use_markitdown
        self.ocr_mode = ocr_mode
        self.pdf_engine = pdf_engine

    def run(self):
        from converter.kb_pipeline import KnowledgeBasePipeline

        pipeline = KnowledgeBasePipeline()
        try:
            result = pipeline.ingest_to_vault(
                self.files,
                self.vault_dir,
                dest_subdir=self.dest_subdir,
                use_markitdown=self.use_markitdown,
                ocr_mode=self.ocr_mode,
                pdf_engine=self.pdf_engine,
            )
            self.finished.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.window.title)
        self.setGeometry(100, 100, config.window.width, config.window.height)
        self.setMinimumSize(config.window.min_width, config.window.min_height)
        self.setAcceptDrops(True)

        detected = detect_obsidian_vault() or ""
        self.vault_dir = detected
        self.dest_subdir = default_vault_dest(detected) if detected else "01-raw/inbox"

        self._init_ui()
        self._setup_logging()

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.ExtendedSelection)

        file_buttons = QHBoxLayout()
        self.add_files_button = QPushButton("添加文件")
        self.add_folder_button = QPushButton("添加文件夹")
        self.remove_files_button = QPushButton("移除选中")
        self.clear_files_button = QPushButton("清空列表")
        for button in (
            self.add_files_button,
            self.add_folder_button,
            self.remove_files_button,
            self.clear_files_button,
        ):
            file_buttons.addWidget(button)

        left_layout.addWidget(QLabel("待投递文件："))
        left_layout.addWidget(self.file_list_widget)
        left_layout.addLayout(file_buttons)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        tabs = QTabWidget()

        settings_tab = QWidget()
        form = QFormLayout(settings_tab)

        self.vault_edit = QLineEdit(self.vault_dir)
        self.vault_edit.setReadOnly(True)
        self.vault_edit.setPlaceholderText("未检测到 Obsidian vault")
        self.browse_vault_button = QPushButton("选择…")
        vault_row = QHBoxLayout()
        vault_row.addWidget(self.vault_edit)
        vault_row.addWidget(self.browse_vault_button)
        form.addRow("目标 vault：", vault_row)

        self.dest_edit = QLineEdit(self.dest_subdir)
        self.dest_edit.setPlaceholderText("01-raw/inbox")
        form.addRow("收件箱：", self.dest_edit)

        self.ocr_combo = QComboBox()
        self.ocr_combo.addItem("自动（安装了 ocrmypdf 就执行）", "auto")
        self.ocr_combo.addItem("关闭", "off")
        form.addRow("扫描 PDF OCR：", self.ocr_combo)

        self.pdf_engine_combo = QComboBox()
        self.pdf_engine_combo.addItem("自动（pdfplumber）", "auto")
        self.pdf_engine_combo.addItem("MarkItDown（更干净，可能丢标题）", "markitdown")
        form.addRow("PDF 引擎：", self.pdf_engine_combo)

        self.markitdown_check = QCheckBox("优先使用 MarkItDown")
        form.addRow("", self.markitdown_check)

        form.addRow("", QLabel("文件会去重、原子写入；同名冲突不会覆盖。"))

        self.ingest_button = QPushButton("转换并投递")
        self.ingest_button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.open_inbox_button = QPushButton("打开收件箱")

        right_layout.addWidget(tabs)
        right_layout.addWidget(self.ingest_button)
        right_layout.addWidget(self.open_inbox_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        tabs.addTab(settings_tab, "投递设置")

        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_widget_handler = QTextEditLogger(self)
        log_layout.addWidget(self.log_widget_handler.widget)
        tabs.addTab(log_tab, "运行日志")

        splitter.addWidget(right_panel)
        splitter.setSizes([self.width() // 2, self.width() // 2])

        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.remove_files_button.clicked.connect(self.remove_files)
        self.clear_files_button.clicked.connect(self.clear_files)
        self.browse_vault_button.clicked.connect(self.browse_vault)
        self.ingest_button.clicked.connect(self.start_ingest)
        self.open_inbox_button.clicked.connect(self.open_inbox)

        if not self.vault_dir:
            self.ingest_button.setEnabled(False)

    def _setup_logging(self):
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        config.setup_logging()

        log_formatter = logging.Formatter(config.logging.format)
        self.log_widget_handler.setFormatter(log_formatter)
        root_logger.addHandler(self.log_widget_handler)

        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("pdfplumber").setLevel(logging.WARNING)
        logger.info("%s v%s 已启动", config.app.name, config.app.version)

    def _add_paths(self, paths):
        existing = {
            self.file_list_widget.item(i).text()
            for i in range(self.file_list_widget.count())
        }
        for path in paths:
            path = str(path)
            if path in existing or not is_supported_file(path):
                continue
            self.file_list_widget.addItem(path)
            existing.add(path)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "文档 (*.pdf *.docx *.xlsx *.md *.markdown *.html *.htm *.txt)",
        )
        self._add_paths(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        files = [
            str(path)
            for path in Path(folder).rglob("*")
            if path.is_file() and is_supported_file(str(path))
        ]
        self._add_paths(files)
        if files:
            QMessageBox.information(self, "完成", f"已添加 {len(files)} 个文件")

    def remove_files(self):
        for item in self.file_list_widget.selectedItems():
            self.file_list_widget.takeItem(self.file_list_widget.row(item))

    def clear_files(self):
        self.file_list_widget.clear()

    def browse_vault(self):
        start = self.vault_dir or str(Path.home() / "Documents")
        folder = QFileDialog.getExistingDirectory(self, "选择 Obsidian vault", start)
        if not folder:
            return
        self.vault_dir = folder
        self.vault_edit.setText(folder)
        self.dest_edit.setText(default_vault_dest(folder))
        self.ingest_button.setEnabled(True)

    def start_ingest(self):
        if self.file_list_widget.count() == 0:
            QMessageBox.warning(self, "提示", "请先添加要投递的文件")
            return

        vault = self.vault_edit.text().strip()
        if not vault or not Path(vault).is_dir():
            QMessageBox.warning(self, "提示", "请选择有效的 Obsidian vault")
            return

        dest = self.dest_edit.text().strip()
        if not dest:
            QMessageBox.warning(self, "提示", "请填写收件箱目录")
            return
        dest_path = Path(dest)
        if dest_path.is_absolute() or ".." in dest_path.parts:
            QMessageBox.warning(self, "提示", "收件箱必须是 vault 内的相对路径")
            return

        files = [
            self.file_list_widget.item(i).text()
            for i in range(self.file_list_widget.count())
        ]
        self.vault_dir = vault
        self.dest_subdir = dest
        self.ingest_button.setEnabled(False)
        self.ingest_button.setText("投递中...")
        self.open_inbox_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)

        self.ingest_thread = QThread(self)
        self.ingest_worker = IngestWorker(
            files,
            vault,
            dest,
            self.markitdown_check.isChecked(),
            self.ocr_combo.currentData(),
            self.pdf_engine_combo.currentData(),
        )
        self.ingest_worker.moveToThread(self.ingest_thread)
        self.ingest_thread.started.connect(self.ingest_worker.run)
        self.ingest_worker.finished.connect(self.ingest_done)
        self.ingest_worker.failed.connect(self.ingest_failed)
        self.ingest_worker.finished.connect(self.ingest_thread.quit)
        self.ingest_worker.failed.connect(self.ingest_thread.quit)
        self.ingest_thread.finished.connect(self.ingest_finished)
        self.ingest_thread.finished.connect(self.ingest_thread.deleteLater)
        self.ingest_thread.start()

    def ingest_done(self, result):
        converted = len(result.get("converted", []))
        skipped = len(result.get("skipped", []))
        failed = result.get("failed", [])
        total = result.get("total_files", 0)
        output_dir = result.get("output_dir", "")

        message = (
            f"转换并投递完成：\n"
            f"成功 {converted}，跳过 {skipped}，失败 {len(failed)}，共 {total}\n"
            f"目标：{output_dir}"
        )
        if failed:
            message += "\n\n失败文件："
            for item in failed[:5]:
                message += f"\n• {Path(item['file']).name}: {item['error'][:80]}"
            QMessageBox.warning(self, "部分完成", message)
        else:
            QMessageBox.information(self, "完成", message)
        logger.info(
            "投递完成：成功 %s，跳过 %s，失败 %s，共 %s",
            converted,
            skipped,
            len(failed),
            total,
        )

    def ingest_failed(self, error):
        QMessageBox.critical(self, "投递失败", f"投递过程中发生错误：\n{error}")
        logger.error("投递失败: %s", error)

    def ingest_finished(self):
        self.ingest_button.setEnabled(True)
        self.ingest_button.setText("转换并投递")
        self.open_inbox_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

    def open_inbox(self):
        vault = self.vault_edit.text().strip()
        dest = self.dest_edit.text().strip()
        if not vault or not dest:
            return
        path = Path(vault) / dest
        if not path.exists():
            QMessageBox.information(self, "提示", "收件箱还不存在，先投递一次文件")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if not local:
                continue
            path = Path(local)
            if path.is_file() and is_supported_file(str(path)):
                paths.append(str(path))
            elif path.is_dir():
                paths.extend(
                    str(p)
                    for p in path.rglob("*")
                    if p.is_file() and is_supported_file(str(p))
                )
        self._add_paths(paths)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
