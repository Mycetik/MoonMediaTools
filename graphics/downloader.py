import os
from PyQt6.QtWidgets import (QLabel, QLineEdit, QPushButton,
                             QRadioButton, QCheckBox, QApplication,
                             QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from logger.logger import log
from managers.graphics.base import BaseScreen


class DownloadWorkerSignals(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)


class DownloaderScreen(BaseScreen):
    def __init__(self, parent, window_manager):
        super().__init__(parent, window_manager)
        self.download_manager = window_manager.download_manager
        self.compress_manager = window_manager.compress_manager

        self.current_operation = None

        self.signals = DownloadWorkerSignals()
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
        self.btn_back.setStyleSheet(
            "background-color: #444444; color: white; border: none; border-radius: 4px; font-weight: bold;")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.go_back)

        self.lbl_status = QLabel("Введіть посилання на відео")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: white; font-size: 18px; font-weight: bold; font-family: sans-serif;")

        top_layout.addWidget(self.btn_back)
        top_layout.addWidget(self.lbl_status, stretch=1)
        top_layout.addSpacing(80)
        main_layout.addLayout(top_layout)
        main_layout.addSpacing(10)

        save_layout = QHBoxLayout()
        save_layout.setContentsMargins(40, 0, 40, 0)

        lbl_save = QLabel("Зберегти в:")
        lbl_save.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")

        self.entry_save_dir = QLineEdit()
        self.entry_save_dir.setFixedHeight(35)
        self.entry_save_dir.setReadOnly(True)
        self.entry_save_dir.setStyleSheet(
            "background-color: #2b2b2b; color: #aaaaaa; border: 1px solid #555; border-radius: 4px; padding-left: 5px; font-size: 13px;")

        default_dir = os.path.join(os.path.expanduser("~"))
        saved_dir = self.window_manager.settings.value("downloader_save_dir", default_dir, type=str)
        if saved_dir and os.path.exists(saved_dir):
            self.entry_save_dir.setText(saved_dir)
        else:
            self.entry_save_dir.setText(default_dir)

        self.btn_browse = QPushButton("Змінити")
        self.btn_browse.setFixedSize(90, 35)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setStyleSheet(
            "background-color: #555555; color: white; border: none; border-radius: 4px; font-weight: bold;")
        self.btn_browse.clicked.connect(self.browse_folder)

        save_layout.addWidget(lbl_save)
        save_layout.addWidget(self.entry_save_dir)
        save_layout.addWidget(self.btn_browse)
        main_layout.addLayout(save_layout)
        main_layout.addSpacing(10)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(40, 0, 40, 0)
        self.entry_url = QLineEdit()
        self.entry_url.setFixedHeight(35)
        self.entry_url.setStyleSheet(
            "background-color: #3c3f41; color: white; border: 1px solid #555; border-radius: 4px; padding-left: 5px; font-size: 14px;")

        self.btn_paste = QPushButton("Вставити")
        self.btn_paste.setFixedSize(90, 35)
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #45a049; }")
        self.btn_paste.clicked.connect(self.paste_clipboard)

        input_layout.addWidget(self.entry_url)
        input_layout.addWidget(self.btn_paste)
        main_layout.addLayout(input_layout)
        main_layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        self.btn_action = QPushButton("Завантажити")
        self.btn_action.setFixedSize(490, 45)
        self.btn_action.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_action.clicked.connect(self.on_download_click)
        self._set_btn_action_style("action", self.btn_action)
        btn_layout.addWidget(self.btn_action, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(btn_layout)
        main_layout.addSpacing(15)

        options_layout = QGridLayout()
        options_layout.setContentsMargins(40, 0, 40, 0)
        options_layout.setHorizontalSpacing(60)
        options_layout.setVerticalSpacing(10)

        option_style = "color: white; font-size: 14px; font-family: sans-serif;"

        self.rb_audio = QRadioButton("Тільки аудіо")
        self.rb_audio.setStyleSheet(option_style)

        self.rb_video = QRadioButton("Відео з найвищою якістю")
        self.rb_video.setStyleSheet(option_style)
        self.rb_video.setChecked(True)

        self.cb_discord = QCheckBox("Стиснути для Discord (< 10 МБ)")
        self.cb_discord.setStyleSheet(option_style)

        self.cb_thumb = QCheckBox("Тільки прев'ю")
        self.cb_thumb.setStyleSheet(option_style)

        self.cb_playlist = QCheckBox("Завантаження плейлистів")
        self.cb_playlist.setStyleSheet(option_style)

        self.cb_max_1080p = QCheckBox("Максимум 1080p")
        self.cb_max_1080p.setStyleSheet(option_style)
        self.cb_max_1080p.setChecked(True)

        self.cb_playlist.stateChanged.connect(self._update_ui_state)
        self.cb_thumb.stateChanged.connect(self._update_ui_state)

        options_layout.addWidget(self.rb_audio, 0, 0)
        options_layout.addWidget(self.cb_thumb, 0, 1)
        options_layout.addWidget(self.rb_video, 1, 0)
        options_layout.addWidget(self.cb_playlist, 1, 1)
        options_layout.addWidget(self.cb_discord, 2, 0)
        options_layout.addWidget(self.cb_max_1080p, 2, 1)

        main_layout.addLayout(options_layout)
        main_layout.addStretch()

    def _update_ui_state(self):
        is_thumb = self.cb_thumb.isChecked()
        is_playlist = self.cb_playlist.isChecked()

        if is_thumb:
            self.rb_audio.setEnabled(False)
            self.rb_video.setEnabled(False)
            self.cb_max_1080p.setEnabled(False)
            self.cb_discord.setEnabled(False)
            self.cb_discord.setChecked(False)
        else:
            self.rb_audio.setEnabled(True)
            self.rb_video.setEnabled(True)
            self.cb_max_1080p.setEnabled(True)

            if is_playlist:
                self.cb_discord.setEnabled(False)
                self.cb_discord.setChecked(False)
            else:
                self.cb_discord.setEnabled(True)

        for widget in [self.rb_audio, self.rb_video, self.cb_max_1080p, self.cb_discord]:
            if widget.isEnabled():
                widget.setStyleSheet("color: white; font-size: 14px; font-family: sans-serif;")
            else:
                widget.setStyleSheet("color: gray; font-size: 14px; font-family: sans-serif;")

    def _on_playlist_toggled(self):
        if self.cb_playlist.isChecked():
            self.cb_discord.setChecked(False)
            self.cb_discord.setEnabled(False)
            self.cb_discord.setStyleSheet("color: gray; font-size: 14px; font-family: sans-serif;")
        else:
            self.cb_discord.setEnabled(True)
            self.cb_discord.setStyleSheet("color: white; font-size: 14px; font-family: sans-serif;")

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Виберіть папку для збереження", self.entry_save_dir.text())
        if folder:
            self.entry_save_dir.setText(folder)
            self.window_manager.settings.setValue("downloader_save_dir", folder)

    def go_back(self):
        self.disable_screen_events()
        if self.current_operation == "download":
            self.download_manager.cancel_download()
        elif self.current_operation == "compress":
            self.compress_manager.cancel_task()

        from managers.graphics.main_menu import MainMenuScreen
        self.window_manager.show_screen(MainMenuScreen)

    def paste_clipboard(self):
        clipboard = QApplication.clipboard()
        self.entry_url.setText(clipboard.text())

    def on_download_click(self):
        url = self.entry_url.text().strip()
        if not url:
            self._update_status("Посилання не може бути пустим!", "orange", self.lbl_status)
            return

        self.current_operation = "download"
        self._update_status("Підготовка...", "yellow", self.lbl_status)
        self._set_btn_action_style("cancel", self.btn_action)
        self.btn_action.setText("Скасувати")
        self.btn_action.clicked.disconnect()
        self.btn_action.clicked.connect(self.on_cancel_click)

        options = {
            "type": "video" if self.rb_video.isChecked() else "audio",
            "thumbnail": self.cb_thumb.isChecked(),
            "playlist": self.cb_playlist.isChecked(),
            "discord": self.cb_discord.isChecked(),
            "max_1080p": self.cb_max_1080p.isChecked(),
            "save_dir": self.entry_save_dir.text().strip()
        }

        self.download_manager.start_download(
            url=url, options=options,
            progress_cb=lambda msg: self.safe_emit(self.signals.progress, msg),
            finish_cb=lambda msg, path: self.safe_emit(self.signals.finished, msg, path),
            error_cb=lambda msg: self.safe_emit(self.signals.error, msg)
        )

    def on_cancel_click(self):
        if self.current_operation == "download":
            self.download_manager.cancel_download()
        elif self.current_operation == "compress":
            self.compress_manager.cancel_task()

    @pyqtSlot(str)
    def _on_progress(self, msg: str):
        self._update_status(msg, "yellow", self.lbl_status)

    @pyqtSlot(str, str)
    def _on_finish(self, msg: str, filepath: str):
        if not self.isVisible(): return

        if self.current_operation == "download" and self.cb_discord.isChecked() and os.path.isfile(filepath):
            self.current_operation = "compress"
            self._update_status("Стиснення для Discord...", "yellow", self.lbl_status)

            base, ext = os.path.splitext(filepath)
            discord_output = f"{base}_discord{ext}"

            self.compress_manager.start_compression(
                input_file=filepath,
                output_file=discord_output,
                target_size_mb=9.9,
                allow_resize=True,
                progress_cb=lambda p_msg: self.safe_emit(self.signals.progress, p_msg),
                finish_cb=lambda f_msg, p_path: self.safe_emit(self.signals.finished, "Успішно стиснено для Discord",
                                                               p_path),
                error_cb=lambda e_msg: self.safe_emit(self.signals.error, e_msg)
            )
            return

        self._update_status(msg, "#90EE90", self.lbl_status)
        self._reset_button()
        self.entry_url.clear()
        self.show_info_msgbox("Успіх!", f"Файл збережено:\n\n{filepath}")

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        if not self.isVisible(): return

        is_compress_error = (self.current_operation == "compress")

        self._reset_button()

        if is_compress_error:
            if "скасовано" in msg.lower():
                self._update_status("Завантажено (Стиснення скасовано)", "orange", self.lbl_status)
                self.show_info_msgbox("Увага", "Оригінальне відео збережено, але стиснення відео було скасовано")
            else:
                self._update_status("Завантажено без стиснення", "orange", self.lbl_status)
                self.show_info_msgbox("Завантажено успішно, але з нюансом",
                                      f"Оригінальне відео успішно завантажено, проте його не вдалося стиснути:\n\n{msg}")

            self.entry_url.clear()
            return

        if "скасовано" in msg.lower():
            self._update_status("Скасовано", "orange", self.lbl_status)
        elif msg == "BLOCKED":
            self._update_status("Помилка захисту", "red", self.lbl_status)
            self.show_info_msgbox("Упс! Привіт від жадібності корпорацій!",
                                  "Завантаження цього відео тимчасово не працює.\n\n"
                                  "YouTube, TikTok (та інші) постійно оновлюють свій захист.\n"
                                  "Платформи не зробили нормальне API, тому усе працює криво.\n"
                                  "Зараз триває процес реверс інженерії їх говносайтів.\n\n Спробуйте завантажити це відео пізніше")
        elif msg == "TIKTOK_PHOTO":
            self._update_status("Формат не підтримується", "red", self.lbl_status)
            self.show_info_msgbox("Помилка",
                                  "Програма не підтримує завантаження фотоколекцій(слайдшоу) через складність їх реверс інженерингу :(")
        elif msg == "DRM":
            self._update_status("Захищено авторським правом", "red", self.lbl_status)
            self.show_error_msgbox("Захист", "Це відео має DRM-захист від піратства. Завантажити його неможливо")
        elif msg == "PRIVATE":
            self._update_status("Відео недоступне", "red", self.lbl_status)
            self.show_error_msgbox("Помилка доступу", "Це відео є приватним, прихованим або було видалене автором")
        elif msg == "AGE_RESTRICTED":
            self._update_status("Вікове обмеження", "red", self.lbl_status)
            self.show_error_msgbox("Обмеження 18+",
                                   "Це відео має вікові обмеження. Сайт не хоче нам його віддавати без авторизації")
        elif msg == "GEO_RESTRICTED":
            self._update_status("Геоблокування", "red", self.lbl_status)
            self.show_error_msgbox("Блокування регіону", "Автор заборонив перегляд цього відео у вашій країні")
        elif msg == "RATE_LIMIT":
            self._update_status("Ліміт запитів (429)", "red", self.lbl_status)
            self.show_error_msgbox("Перевищено ліміт",
                                   "Платформа образилась що ви робили занадто багато запитів і тимчасово заблокувала вашу IP-адресу(HTTP 429).\n\nМожна зачекати поки бан пройде, або використати VPN")
        elif msg == "MEMBERS_ONLY":
            self._update_status("Платне відео", "red", self.lbl_status)
            self.show_error_msgbox("Ексклюзив для спонсорів",
                                   "Це відео доступне лише для спонсорів")
        elif msg == "PREMIERE":
            self._update_status("Трансляція ще не почалася", "orange", self.lbl_status)
            self.show_info_msgbox("Очікування",
                                  "Це відео є запланованою трансляцією або прем'єрою, яка ще не почалася. Спробуйте пізніше")
        elif msg == "UNSUPPORTED_URL":
            self._update_status("Невідоме посилання", "red", self.lbl_status)
            self.show_error_msgbox("Помилка", "Програма не розпізнає це посилання, перевірте його")
        else:
            self._update_status("Невідома помилка", "red", self.lbl_status)
            self.show_error_msgbox("Виникла невідома помилка :(", msg)

    def _reset_button(self):
        if not self.isVisible(): return
        self.current_operation = None
        self._set_btn_action_style("action", self.btn_action)
        self.btn_action.setText("Завантажити")
        try:
            self.btn_action.clicked.disconnect()
        except TypeError:
            pass
        self.btn_action.clicked.connect(self.on_download_click)