import yaml
from logger.logger import log

def read_config():
    try:
        with open('config.yml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        version = config['program']['version']
        displayname = config['program']['displayname']
        verbose_ytdlp = config['program'].get('verbose_ytdlp', False)

    except FileNotFoundError:
        log.fatal("config.yml not found!")

    except Exception as e:
        log.fatal(f"Config read error: {e}")

    return version, displayname, verbose_ytdlp