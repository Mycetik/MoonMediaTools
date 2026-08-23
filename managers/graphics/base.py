import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from PyQt6.QtCore import QSettings
from logger.logger import log


class WindowManager:
    def __init__(self, title: str, version: str):
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)

        self.window = QMainWindow()
        self.window.setWindowTitle(f"{title} v{version}")
        self.window.setFixedSize(600, 350)
        self.window.setStyleSheet("background-color: #2b2b2b;")

        self.settings = QSettings("MoonMediaTools")

        self.download_manager = None
        self.convert_manager = None
        self.compress_manager = None
        self.current_screen = None

    def set_download_manager(self, manager): self.download_manager = manager

    def set_convert_manager(self, manager): self.convert_manager = manager

    def set_compress_manager(self, manager): self.compress_manager = manager

    def show_screen(self, ScreenClass):
        log.info(f"Switching GUI to: {ScreenClass.__name__}")
        self.current_screen = ScreenClass(self.window, self)
        self.window.setCentralWidget(self.current_screen)

    def run(self):
        log.info("PyQt6 started")
        self.window.show()
        self.app.exec()

class BaseScreen(QWidget):
    def __init__(self, parent, window_manager):
        super().__init__(parent)
        self.window_manager = window_manager
        self._is_active = [True]

    def _update_status(self, msg: str, color: str, label_widget):
        if not self.isVisible() or not self._is_active[0]: return
        label_widget.setText(msg)
        label_widget.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; font-family: sans-serif;")

    def _set_btn_action_style(self, state: str, btn_widget):
        if state == "action":
            btn_widget.setStyleSheet("""
                QPushButton { background-color: #007BFF; color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 14px; }
                QPushButton:hover { background-color: #0056b3; }
            """)
        elif state == "cancel":
            btn_widget.setStyleSheet("""
                QPushButton { background-color: #dc3545; color: white; border: none; border-radius: 5px; font-weight: bold; font-size: 14px; }
                QPushButton:hover { background-color: #c82333; }
            """)

    def safe_emit(self, signal, *args):
        if self._is_active[0]:
            signal.emit(*args)

    def show_error_msgbox(self, title, text):
        if self.isVisible() and self._is_active[0]:
            QMessageBox.critical(self, title, text)

    def show_info_msgbox(self, title, text):
        if self.isVisible() and self._is_active[0]:
            QMessageBox.information(self, title, text)

    def disable_screen_events(self):
        self._is_active[0] = False