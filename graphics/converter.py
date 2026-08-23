import os
from PyQt6.QtWidgets import (QLabel, QPushButton, QComboBox, QLineEdit,
                             QCheckBox, QFileDialog, QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot

from managers.graphics.base import BaseScreen


class ConvertWorkerSignals(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)


class ConverterScreen(BaseScreen):
    def __init__(self, parent, window_manager):
        super().__init__(parent, window_manager)
        self.convert_manager = window_manager.convert_manager

        self.input_file = None
        self.setAcceptDrops(True)

        self.signals = ConvertWorkerSignals()
        self.signals.progress.connect(self._on_progress)
        self.signals.finished.connect(self._on_finish)
        self.signals.error.connect(self._on_error)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

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

        saved_dir = self.window_manager.settings.value("converter_save_dir", "", type=str)
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

        main_layout.addSpacing(15)

        frm_options = QHBoxLayout()

        lbl_format = QLabel("Новий формат:")
        lbl_format.setStyleSheet("color: white; font-size: 14px; font-family: sans-serif;")

        self.cb_format = QComboBox()
        formats = [".mp4", ".mkv", ".avi", ".mp3", ".wav", ".gif", ".flac", ".ogg"]
        self.cb_format.addItems(formats)
        self.cb_format.setFixedSize(80, 30)
        self.cb_format.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_format.setStyleSheet("""
            QComboBox { background-color: #3c3f41; color: white; border: 1px solid #555; border-radius: 3px; padding-left: 10px; font-size: 14px; }
            QComboBox::drop-down { border: none; }
        """)

        frm_options.addStretch()
        frm_options.addWidget(lbl_format)
        frm_options.addSpacing(10)
        frm_options.addWidget(self.cb_format)
        frm_options.addStretch()
        main_layout.addLayout(frm_options)

        gpu_layout = QHBoxLayout()
        self.cb_gpu = QCheckBox("Використовувати GPU")
        self.cb_gpu.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cb_gpu.setStyleSheet("color: white; font-size: 14px; font-family: sans-serif; ")

        gpu_saved_state = self.window_manager.settings.value("converter_use_gpu", False, type=bool)
        self.cb_gpu.setChecked(gpu_saved_state)
        self.cb_gpu.stateChanged.connect(
            lambda: self.window_manager.settings.setValue("converter_use_gpu", self.cb_gpu.isChecked())
        )

        gpu_layout.addWidget(self.cb_gpu, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(gpu_layout)

        main_layout.addSpacing(20)

        action_layout = QHBoxLayout()
        self.btn_action = QPushButton("Конвертувати")
        self.btn_action.setFixedSize(410, 40)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self.start_conversion)
        self._set_btn_action_style("action", self.btn_action)
        action_layout.addWidget(self.btn_action, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(action_layout)

        main_layout.addSpacing(10)

        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: yellow; font-size: 14px; font-family: sans-serif;")
        main_layout.addWidget(self.lbl_status)
        main_layout.addStretch()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            filepath = urls[0].toLocalFile()
            valid_exts = ('.mp4', '.mkv', '.avi', '.mov', '.gif', '.mp3', '.wav', '.flac', '.webm', '.ogg', '.m4a', '.png', '.jpg', '.jpeg')

            if filepath.lower().endswith(valid_exts):
                self._set_input_file(filepath)
            else:
                self._update_status("Цей формат не підтримується!", "red", self.lbl_status)

    def select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Оберіть медіафайл", "",
            "Media files (*.mp4 *.mkv *.avi *.mov *.gif *.mp3 *.wav *.flac *.webm *.ogg *.m4a *.png *.jpg *.jpeg);;All Files (*)"
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

        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.png', '.jpg', '.jpeg', '.mp4']:
            self.cb_format.setCurrentText(".gif")

    def change_save_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Виберіть папку для збереження", self.entry_save_dir.text())
        if folder:
            self.entry_save_dir.setText(folder)
            self.window_manager.settings.setValue("converter_save_dir", folder)

    def start_conversion(self):
        if not self.input_file:
            self._update_status("Спочатку оберіть файл!", "orange", self.lbl_status)
            return

        out_format = self.cb_format.currentText()
        in_ext = os.path.splitext(self.input_file)[1].lower()

        if in_ext == out_format.lower():
            self.show_info_msgbox("Альцгеймер детектет!",
                                  f"Файл вже має формат {out_format}, конвертація не потрібна")
            self._update_status("Скасовано", "orange", self.lbl_status)
            return

        out_format = self.cb_format.currentText()
        save_dir = self.entry_save_dir.text()
        base_name = os.path.splitext(os.path.basename(self.input_file))[0]
        output_file = os.path.join(save_dir, f"{base_name}_converted{out_format}")

        self._set_btn_action_style("cancel", self.btn_action)
        self.btn_action.setText("Скасувати")
        self.btn_action.clicked.disconnect()
        self.btn_action.clicked.connect(self.cancel_conversion)

        self.convert_manager.start_conversion(
            input_file=self.input_file,
            output_file=output_file,
            use_gpu=self.cb_gpu.isChecked(),
            progress_cb=lambda msg: self.safe_emit(self.signals.progress, msg),
            finish_cb=lambda msg, path: self.safe_emit(self.signals.finished, msg, path),
            error_cb=lambda msg: self.safe_emit(self.signals.error, msg)
        )

    def cancel_conversion(self):
        self.convert_manager.cancel_task()

    def go_back(self):
        self.disable_screen_events()
        self.convert_manager.cancel_task()

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
        self.show_info_msgbox("Успіх!", f"Файл успішно оброблено та збережено:\n\n{filepath}")

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        if not self.isVisible(): return

        if msg == "Скасовано користувачем":
            self._update_status("Скасовано", "orange", self.lbl_status)
        else:
            self._update_status("Помилка конвертації", "red", self.lbl_status)
            self.show_error_msgbox("Помилка", msg)

        self._reset_button()

    def _reset_button(self):
        if not self.isVisible(): return
        self._set_btn_action_style("action", self.btn_action)
        self.btn_action.setText("Конвертувати")
        try:
            self.btn_action.clicked.disconnect()
        except TypeError:
            pass
        self.btn_action.clicked.connect(self.start_conversion)