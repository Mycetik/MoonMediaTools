from logger.logger import log
from libs.library_manager import install_libraries

def main():
    # Того, хто придумав писати yt-dlp на довбаному python хочеться обняти дуже міцно, поки хруст не буде чутно.
    # Я тепер змушений писати повноцінну програму в мові програмування, яка не призначена ні для чого окрім маленьких скриптів.

    # Спочатку я хотів зробити в програмі нормальну архітектуру,
    # але я витратив більшість часу на битву з дебілізмами в python.
    # Тепер вже зробив як зробив, самі б спробували

    try:
        log.info("Checking dependencies...")
        install_libraries("libs.txt")
        log.info("Importing dependencies...")

        from util.read_config import read_config
        import startup

    except Exception as e:
        log.fatal(f"Critical error while updating dependencies: {e}")


    version, displayname, verbose_ytdlp = read_config()

    startup.start(version, displayname, verbose_ytdlp)

if __name__ == '__main__':
    main()
