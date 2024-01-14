import logging
import os
import sys
from abc import ABC
from pathlib import Path

from home_automations.const import DEFAULT_LOGGING_PATH, ENV_LOG_FILE_PATH
from home_automations.models.config import Config


class Logger(ABC):
    @classmethod
    async def init(cls, config: Config):
        log_file_path = Path(
            config.logging.path or os.getenv(ENV_LOG_FILE_PATH) or DEFAULT_LOGGING_PATH
        )

        if not log_file_path.is_absolute():
            log_file_path = config.config_file_path.parent / log_file_path

        logging.basicConfig(
            level=config.logging.level.upper()
            if isinstance(config.logging.level, str)
            else config.logging.level,
            format=config.logging.format,
            datefmt=config.logging.datefmt,
            handlers=[
                logging.FileHandler(log_file_path, mode=config.logging.filemode),
                logging.StreamHandler(sys.stdout),
            ],
        )

        logging.getLogger("apscheduler.executors.default").disabled = True
        logging.getLogger("apscheduler.scheduler").propagate = False
        logging.getLogger("hass_client").propagate = False
