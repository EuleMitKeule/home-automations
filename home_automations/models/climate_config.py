from dataclasses import dataclass, field

from home_automations.const import DEFAULT_MAX_TARGET_TEMP, DEFAULT_MIN_TARGET_TEMP
from home_automations.models.thermostat_config import ThermostatConfig


@dataclass
class ClimateConfig:
    thermostat_configs: list[ThermostatConfig] = field(
        metadata={"data_key": "thermostat"}
    )
    schedule: dict[str, float]
    min_target_temp: float = DEFAULT_MIN_TARGET_TEMP
    max_target_temp: float = DEFAULT_MAX_TARGET_TEMP
