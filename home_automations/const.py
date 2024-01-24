from enum import Enum, StrEnum

ENV_CONFIG_FILE_PATH = "CONFIG_FILE_PATH"
DEFAULT_CONFIG_FILE_PATH = "config.yml"

ENV_LOG_FILE_PATH = "LOG_FILE_PATH"

DEFAULT_LOGGING_LEVEL = "info"
DEFAULT_LOGGING_PATH = "home_automations.log"
DEFAULT_LOGGING_FMT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_LOGGING_DATEFMT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOGGING_FILEMODE = "a"

DEFAULT_TZ = "Europe/Berlin"

DEFAULT_MAX_THERMOSTAT_TEMP = 29.5
DEFAULT_MIN_THERMOSTAT_TEMP = 4.5
DEFAULT_MAX_EFFECTIVE_THERMOSTAT_TEMP = 29.0
DEFAULT_MIN_EFFECTIVE_THERMOSTAT_TEMP = 17.5
DEFAULT_MAX_TARGET_DIFF = 4.5

DEFAULT_TIBBER_UPDATE_INTERVAL = 60

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000


class ThermostatState(str, Enum):
    OFF = "off"
    HEAT = "heat"
    AUTO = "auto"
    UNAVAILABLE = "unavailable"


class TibberLevel(StrEnum):
    VERY_EXPENSIVE = "VERY_EXPENSIVE"
    EXPENSIVE = "EXPENSIVE"
    NORMAL = "NORMAL"
    CHEAP = "CHEAP"
    VERY_CHEAP = "VERY_CHEAP"
    FREE = "FREE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.lower() == value:
                return member
            if member.upper() == value:
                return member
        return None
