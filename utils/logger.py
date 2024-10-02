# utils/logger.py

import logging
from typing import Dict

class Logger:
    _instances: Dict[str, 'Logger'] = {}

    @classmethod
    def get_instance(cls, name: str) -> 'Logger':
        if name not in cls._instances:
            cls._instances[name] = cls(name)
        return cls._instances[name]

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        self.logger.addHandler(ch)

    def debug(self, message: str):
        self.logger.debug(message)

    def info(self, message: str):
        self.logger.info(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def error(self, message: str, exc_info=False):
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str):
        self.logger.critical(message)