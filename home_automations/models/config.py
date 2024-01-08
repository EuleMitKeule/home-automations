import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import marshmallow_dataclass
import yaml
from dataclass_wizard import YAMLWizard

from home_automations.const import DEFAULT_LOGGING_PATH, ENV_LOG_FILE_PATH
from home_automations.helper.clock import Clock
from home_automations.models.homeassistant_config import HomeAssistantConfig
from home_automations.models.logging_config import LoggingConfig
from home_automations.models.thermostat_config import ThermostatConfig


@dataclass
class Config(YAMLWizard):
    """Configuration for the app."""

    config_file_path: Path = field(init=False, repr=False, compare=False)
    timezone: str
    homeassistant: HomeAssistantConfig
    thermostats: list[ThermostatConfig] = field(default_factory=list)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def configure_logging(self):
        """Configure logging."""

        log_file_path = Path(
            self.logging.path or os.getenv(ENV_LOG_FILE_PATH) or DEFAULT_LOGGING_PATH
        )

        if not log_file_path.is_absolute():
            log_file_path = self.config_file_path.parent / log_file_path
            self.logging.path = log_file_path.as_posix()

        logging.basicConfig(
            level=self.logging.level.upper()
            if isinstance(self.logging.level, str)
            else self.logging.level,
            format=self.logging.format,
            datefmt=self.logging.datefmt,
            handlers=[
                logging.FileHandler(log_file_path, mode=self.logging.filemode),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def configure_time(self):
        """Configure time."""

        Clock.set_timezone(self.timezone)

    @classmethod
    def load(cls, file_path: Path) -> Optional["Config"]:
        """Load configuration from YAML file."""

        if not file_path.exists():
            cls.create_default_config(file_path)
            return None

        with file_path.open("r") as yaml_file:
            config_dict = yaml.load(yaml_file, Loader=yaml.FullLoader)

        result: Config = marshmallow_dataclass.class_schema(cls)().load(config_dict)
        result.config_file_path = file_path
        result.configure_logging()
        result.configure_time()

        return result

    @classmethod
    def create_default_config(cls, file_path: Path):
        """Create default configuration file."""

        default_config = cls(
            timezone="Europe/Berlin",
            homeassistant=HomeAssistantConfig(
                url="http://localhost:8123", token="token"
            ),
        )

        default_config.configure_logging()

        with open(file_path, "w") as yaml_file:
            yaml.dump(
                marshmallow_dataclass.class_schema(cls)().dump(default_config),
                yaml_file,
            )

        logging.warning(
            f"Config file {file_path} does not exist, creating default file"
        )
