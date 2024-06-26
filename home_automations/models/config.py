import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import marshmallow_dataclass
import yaml

from home_automations.models.api_config import ApiConfig
from home_automations.models.climate_config import ClimateConfig
from home_automations.models.dimmer_config import DimmerConfig
from home_automations.models.homeassistant_config import HomeAssistantConfig
from home_automations.models.light_replacement_config import LightReplacementConfig
from home_automations.models.logging_config import LoggingConfig
from home_automations.models.motion_light_config import MotionLightConfig
from home_automations.models.sensor_notify_config import SensorNotifyConfig
from home_automations.models.tibber_config import TibberConfig
from home_automations.models.timed_light_config import TimedLightConfig


@dataclass
class Config:
    """Configuration for the app."""

    config_file_path: Path = field(init=False, repr=False, compare=False)
    timezone: str
    homeassistant: HomeAssistantConfig
    tibber: TibberConfig
    climate_configs: list[ClimateConfig] = field(
        default_factory=list, metadata={"data_key": "climate"}
    )
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    dimmer_configs: list[DimmerConfig] = field(default_factory=list)
    timed_light_configs: list[TimedLightConfig] = field(default_factory=list)
    motion_light_configs: list[MotionLightConfig] = field(default_factory=list)
    sensor_notify_configs: list[SensorNotifyConfig] = field(default_factory=list)
    light_replacement_configs: list[LightReplacementConfig] = field(
        default_factory=list
    )

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

    def save(self):
        """Save configuration to YAML file."""

        with self.config_file_path.open("w") as yaml_file:
            yaml.dump(
                marshmallow_dataclass.class_schema(Config)().dump(self),
                yaml_file,
            )

    @classmethod
    def create_default_config(cls, file_path: Path):
        """Create default configuration file."""

        default_config = cls(
            timezone="Europe/Berlin",
            homeassistant=HomeAssistantConfig(
                url="http://localhost:8123", token="token"
            ),
            tibber=TibberConfig(
                token="token",
                home_id="home_id",
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
