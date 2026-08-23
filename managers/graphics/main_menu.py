from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from util.network import is_internet_available
from logger.logger import log

class MainMenuScreen(QWidget):
    def __init__(self, parent, window_manager):
        super().__init__(parent)
        self.window_manager = window_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(100, 20, 100, 20)

        lbl_title = QLabel("MoonMediaTools")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("""
            color: white; 
            font-size: 24px; 
            font-weight: bold; 
            font-family: sans-serif;
            margin-bottom: 20px;
        """)
        layout.addWidget(lbl_title)

        def create_button(text, bg_color, hover_color, text_color="white"):
            btn = QPushButton(text)
            btn.setMinimumHeight(45)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)
            return btn

        btn_download = create_button("Завантаження відео", "#007BFF", "#0056b3")
        btn_download.clicked.connect(self.go_to_downloader)
        layout.addWidget(btn_download)

        btn_convert = create_button("Конвертація медіа", "#007BFF", "#0056b3")
        btn_convert.clicked.connect(self.go_to_converter)
        layout.addWidget(btn_convert)

        btn_compress = create_button("Стиснення медіа", "#007BFF", "#0056b3", "white")
        btn_compress.clicked.connect(self.go_to_compressor)
        layout.addWidget(btn_compress)

    def go_to_downloader(self):
        if not is_internet_available():
            QMessageBox.warning(
                self,
                "Не знайдено підключення до інтернету",
                "Для завантаження відео необхідне підключення до інтернету, а програма його знайти не змогла :("
            )
            return
        log.info("Downloader menu")
        from graphics.downloader import DownloaderScreen
        self.window_manager.show_screen(DownloaderScreen)

    def go_to_converter(self):
        log.info("Converter menu")
        from graphics.converter import ConverterScreen
        self.window_manager.show_screen(ConverterScreen)

    def go_to_compressor(self):
        log.info("Compressor menu")
        from graphics.compressor import CompressorScreen
        self.window_manager.show_screen(CompressorScreen)