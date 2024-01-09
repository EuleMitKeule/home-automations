import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import marshmallow_dataclass
import yaml
from dataclass_wizard import YAMLWizard

from home_automations.models.homeassistant_config import HomeAssistantConfig
from home_automations.models.logging_config import LoggingConfig
from home_automations.models.thermostat_config import ThermostatConfig
from home_automations.models.tibber_config import TibberConfig


@dataclass
class Config(YAMLWizard):
    """Configuration for the app."""

    config_file_path: Path = field(init=False, repr=False, compare=False)
    timezone: str
    homeassistant: HomeAssistantConfig
    thermostats: list[ThermostatConfig] = field(default_factory=list)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    tibber: TibberConfig = field(default_factory=TibberConfig)

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

        with open(file_path, "w") as yaml_file:
            yaml.dump(
                marshmallow_dataclass.class_schema(cls)().dump(default_config),
                yaml_file,
            )

        logging.warning(
            f"Config file {file_path} does not exist, creating default file"
        )
