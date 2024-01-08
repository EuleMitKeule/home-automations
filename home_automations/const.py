import logging
from enum import Enum

ENV_CONFIG_FILE_PATH = "CONFIG_FILE_PATH"
DEFAULT_CONFIG_FILE_PATH = "config.yml"

ENV_LOG_FILE_PATH = "LOG_FILE_PATH"

DEFAULT_LOGGING_LEVEL = logging.INFO
DEFAULT_LOGGING_PATH = "home_automations.log"
DEFAULT_LOGGING_FMT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_LOGGING_DATEFMT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOGGING_FILEMODE = "a"

DEFAULT_TZ = "Europe/Berlin"


class ThermostatState(str, Enum):
    OFF = "off"
    HEAT = "heat"
    AUTO = "auto"
    UNAVAILABLE = "unavailable"
