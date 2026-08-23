import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from logger.logger import log
from media.download_manager import DownloadManager
from managers.graphics.base import WindowManager
from managers.graphics.main_menu import MainMenuScreen
from media.compress_manager import CompressManager
from media.convert_manager import ConvertManager


def start(version: str, displayname: str, verbose_ytdlp: bool = False) -> None:
    log.info(f"Starting {displayname} {version}...")

    def sigint_handler(signum, frame):
        log.warn("Program interrupted by user (CTRL+C). Shutting down...")
        app = QApplication.instance()
        if app:
            app.quit()

    signal.signal(signal.SIGINT, sigint_handler)

    download_manager = DownloadManager()
    download_manager.verbose_ytdlp = verbose_ytdlp
    compress_manager = CompressManager()
    convert_manager = ConvertManager()

    try:
        log.info("Initializing core managers...")

        download_manager.init_if_needed()
        compress_manager.init_if_needed()
        convert_manager.init_if_needed()

        log.info("Initializing GUI...")
        window_manager = WindowManager(displayname, version)
        window_manager.set_download_manager(download_manager)
        window_manager.set_convert_manager(convert_manager)
        window_manager.set_compress_manager(compress_manager)

        window_manager.show_screen(MainMenuScreen)

        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(500)

        log.info("Successfully launched")
        window_manager.run()

    except Exception as e:
        log.fatal(f"App crashed during runtime: {e}")

    finally:
        log.info("Shutting down managers...")

        download_manager.shutdown_if_needed()
        compress_manager.shutdown_if_needed()
        convert_manager.shutdown_if_needed()

        log.info("Goodbye!")