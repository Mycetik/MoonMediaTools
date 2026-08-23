import os
from PyQt6.QtWidgets import (QLabel, QPushButton, QLineEdit,
                             QFileDialog, QVBoxLayout, QHBoxLayout, QCheckBox)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot

from managers.graphics.base import BaseScreen
from logger.logger import log

class CompressWorkerSignals(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)


class CompressorScreen(BaseScreen):
    def __init__(self, parent, window_manager):
        super().__init__(parent, window_manager)
        self.compress_manager = window_manager.compress_manager

        self.input_file = None
        self.setAcceptDrops(True)

        self.signals = CompressWorkerSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.finished.connect(self._on_finish)
        self.signals.error.connect(self._on_error)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        top_layout = QHBoxLayout()
        self.btn_back = QPushButton("< Назад")
        self.btn_back.setFixedSize(80, 30)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet(
            "background-color: #444444; color: white; border: none; border-radius: 4px; font-weight: bold;")
        self.btn_back.clicked.connect(self.go_back)
        top_layout.addWidget(self.btn_back)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        self.lbl_file = QLabel("Перетягніть файл сюди або натисніть 'Оглянути'")
        self.lbl_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_file.setStyleSheet("color: white; font-size: 16px; font-weight: bold; font-family: sans-serif;")
        main_layout.addWidget(self.lbl_file)

        browse_layout = QHBoxLayout()
        self.btn_browse = QPushButton("Оглянути")
        self.btn_browse.setFixedSize(410, 40)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px; border: none; border-radius: 4px; }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_browse.clicked.connect(self.select_file)
        browse_layout.addWidget(self.btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(browse_layout)

        main_layout.addSpacing(10)

        save_layout = QHBoxLayout()
        lbl_save = QLabel("Зберегти в:")
        lbl_save.setStyleSheet("color: white; font-size: 14px; font-family: sans-serif;")

        self.entry_save_dir = QLineEdit()
        self.entry_save_dir.setFixedHeight(30)
        self.entry_save_dir.setReadOnly(True)
        self.entry_save_dir.setPlaceholderText("Директорія вихідного файлу")
        self.entry_save_dir.setStyleSheet(
            "background-color: #2b2b2b; color: #aaaaaa; border: 1px solid #555; border-radius: 3px; padding-left: 5px;")

        saved_dir = self.window_manager.settings.value("compressor_save_dir", "", type=str)
        if saved_dir and os.path.exists(saved_dir):
            self.entry_save_dir.setText(saved_dir)

        self.btn_browse_save = QPushButton("Змінити")
        self.btn_browse_save.setFixedSize(80, 30)
        self.btn_browse_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_save.setStyleSheet(
            "background-color: #555555; color: white; border: none; border-radius: 3px; font-weight: bold;")
        self.btn_browse_save.clicked.connect(self.change_save_dir)

        save_layout.addWidget(lbl_save)
        save_layout.addWidget(self.entry_save_dir)
        save_layout.addWidget(self.btn_browse_save)
        main_layout.addLayout(save_layout)

        frm_size = QHBoxLayout()
        frm_size.setSpacing(10)
        lbl_size = QLabel("Цільовий розмір (МБ):")
        lbl_size.setStyleSheet("color: white; font-size: 14px; font-family: sans-serif;")
        frm_size.addWidget(lbl_size, alignment=Qt.AlignmentFlag.AlignRight)

        self.entry_size = QLineEdit("9")
        self.entry_size.setFixedSize(80, 30)
        self.entry_size.setStyleSheet(
            "background-color: #3c3f41; color: white; border: 1px solid #555; border-radius: 3px; padding-left: 5px; font-size: 14px;")
        frm_size.addWidget(self.entry_size, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addLayout(frm_size)

        self.cb_resize = QCheckBox("Дозволити зменшувати роздільну здатність відео")
        self.cb_resize.setStyleSheet("color: white; font-size: 13px; font-family: sans-serif;")

        resize_saved = self.window_manager.settings.value("compressor_allow_resize", True, type=bool)
        self.cb_resize.setChecked(resize_saved)
        self.cb_resize.stateChanged.connect(
            lambda: self.window_manager.settings.setValue("compressor_allow_resize", self.cb_resize.isChecked())
        )

        main_layout.addWidget(self.cb_resize, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacing(10)

        action_layout = QHBoxLayout()
        self.btn_action = QPushButton("Стиснути")
        self.btn_action.setFixedSize(410, 40)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self.start_compression)

        self.btn_action.setStyleSheet("""
            QPushButton { background-color: #ffc107; color: black; border: none; border-radius: 5px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #e0a800; }
        """)

        action_layout.addWidget(self.btn_action, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(action_layout)

        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_btn_action_style("action", self.btn_action)
        main_layout.addWidget(self.lbl_status)
        main_layout.addStretch()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            filepath = urls[0].toLocalFile()
            valid_exts = ('.mp4', '.gif')

            if filepath.lower().endswith(valid_exts):
                self._set_input_file(filepath)
            else:
                self._update_status("Цей формат не підтримується! Тільки MP4 та GIF", "red", self.lbl_status)

    def select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Оберіть відеофайл", "", "Video files (*.mp4 *.gif)"
        )
        if filepath:
            self._set_input_file(filepath)

    def _set_input_file(self, filepath):
        self.input_file = filepath
        filename = os.path.basename(filepath)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)

        self.lbl_file.setText(f"Файл: {filename} ({size_mb:.1f} MB)")
        self.lbl_file.setStyleSheet("color: #90EE90; font-size: 16px; font-weight: bold; font-family: sans-serif;")

        if not self.entry_save_dir.text():
            self.entry_save_dir.setText(os.path.dirname(filepath))

    def change_save_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Виберіть папку для збереження", self.entry_save_dir.text())
        if folder:
            self.entry_save_dir.setText(folder)
            self.window_manager.settings.setValue("compressor_save_dir", folder)

    def start_compression(self):
        if not self.input_file:
            self._update_status("Спочатку оберіть файл!", "orange", self.lbl_status)
            return

        try:
            target_size = float(self.entry_size.text().replace(',', '.'))
        except ValueError:
            self._update_status("Шо ти за фігню замість розміра ввів?", "red", self.lbl_status)
            return

        save_dir = self.entry_save_dir.text()
        base_name, ext = os.path.splitext(os.path.basename(self.input_file))
        out_ext = ext if ext.lower() == '.gif' else '.mp4'
        output_file = os.path.join(save_dir, f"{base_name}_compressed{out_ext}")

        self._set_btn_action_style("cancel", self.btn_action)
        self.btn_action.setText("Скасувати")
        self.btn_action.clicked.disconnect()
        self.btn_action.clicked.connect(self.cancel_compression)

        self.compress_manager.start_compression(
            input_file=self.input_file,
            output_file=output_file,
            target_size_mb=target_size,
            allow_resize=self.cb_resize.isChecked(),
            progress_cb=lambda msg: self.safe_emit(self.signals.progress, msg),
            finish_cb=lambda msg, path: self.safe_emit(self.signals.finished, msg, path),
            error_cb=lambda msg: self.safe_emit(self.signals.error, msg)
        )

    def cancel_compression(self):
        self.compress_manager.cancel_task()

    def go_back(self):
        self.disable_screen_events()
        self.compress_manager.cancel_task()

        from managers.graphics.main_menu import MainMenuScreen
        self.window_manager.show_screen(MainMenuScreen)

    @pyqtSlot(str)
    def _on_progress(self, msg: str):
        self._update_status(msg, "yellow", self.lbl_status)

    @pyqtSlot(str, str)
    def _on_finish(self, msg: str, filepath: str):
        if not self.isVisible(): return
        self._update_status(msg, "#90EE90", self.lbl_status)
        self._reset_button()
        self.show_info_msgbox("Nice", f"Файл збережено за шляхом:\n\n{filepath}")

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        if not self.isVisible(): return

        if msg == "Скасовано користувачем":
            self._update_status("Скасовано", "orange", self.lbl_status)
        else:
            self._update_status("Помилка стиснення", "red", self.lbl_status)
            self.show_error_msgbox("Помилка", msg)

        self._reset_button()

    def _reset_button(self):
        if not self.isVisible(): return

        self.btn_action.setStyleSheet("""
            QPushButton { background-color: #ffc107; color: black; border: none; border-radius: 5px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #e0a800; }
        """)
        self.btn_action.setText("Стиснути")
        try:
            self.btn_action.clicked.disconnect()
        except TypeError:
            pass
        self.btn_action.clicked.connect(self.start_compression)