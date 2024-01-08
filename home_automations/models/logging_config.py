from dataclasses import dataclass

from home_automations.const import (
    DEFAULT_LOGGING_DATEFMT,
    DEFAULT_LOGGING_FILEMODE,
    DEFAULT_LOGGING_FMT,
    DEFAULT_LOGGING_LEVEL,
)


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    path: str | None = None
    level: str = DEFAULT_LOGGING_LEVEL
    format: str = DEFAULT_LOGGING_FMT
    datefmt: str = DEFAULT_LOGGING_DATEFMT
    filemode: str = DEFAULT_LOGGING_FILEMODE
