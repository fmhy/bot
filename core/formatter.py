import logging
import sys
import logging.handlers
from typing import Any


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self):
        super().__init__()
        INFO_FORMAT = "%(asctime)s (%(name)s) [%(levelname)s]: %(message)s"
        FORMAT = "%(asctime)s (%(name)s) [%(levelname)s]: %(message)s (%(filename)s:%(lineno)d)"

        self.FORMATS = {
            logging.DEBUG: self.grey + FORMAT + self.reset,
            logging.INFO: self.blue + INFO_FORMAT + self.reset,
            logging.WARNING: self.yellow + FORMAT + self.reset,
            logging.ERROR: self.red + FORMAT + self.reset,
            logging.CRITICAL: self.bold_red + FORMAT + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "(%H:%M)")
        return formatter.format(record)


def install(name: str, flavor: Any) -> None:
    # core logger
    logger = logging.getLogger(name)
    logger.setLevel(flavor)

    # Make logging faster
    logging.logThreads = False
    logging.logProcesses = False

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(flavor)

    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)

    # file logging (optional)
    file_handler = logging.handlers.RotatingFileHandler(
        f"logs/{name}.log",
        encoding="utf-8",
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(CustomFormatter())
    logger.addHandler(file_handler)
