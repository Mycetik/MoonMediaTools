import sys
from datetime import datetime

class Logger:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"

    def _print_log(self, level: str, color: str, message: str):
        current_time = datetime.now().strftime("%H:%M:%S")

        print(f"[{current_time} {color}{level}{self.RESET}]: {message}")

    def info(self, message: str):
        self._print_log("INFO", self.GREEN, message)

    def warn(self, message: str):
        self._print_log("WARN", self.YELLOW, message)

    def error(self, message: str):
        self._print_log("ERROR", self.RED, message)

    def fatal(self, message: str):
        self._print_log("FATAL", self.RED, f"\n!PROGRAM PANIC!\nA critical error occurred in the program:\n"+message)
        sys.exit(10)

log = Logger()