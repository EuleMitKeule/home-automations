from dataclasses import dataclass, field

from home_automations.const import (
    DEFAULT_MAX_EFFECTIVE_THERMOSTAT_TEMP,
    DEFAULT_MAX_TARGET_DIFF,
    DEFAULT_MAX_THERMOSTAT_TEMP,
    DEFAULT_MIN_EFFECTIVE_THERMOSTAT_TEMP,
    DEFAULT_MIN_THERMOSTAT_TEMP,
)
from home_automations.models.thermostat_config import ThermostatConfig


@dataclass
class ClimateConfig:
    thermostat_configs: list[ThermostatConfig] = field(
        metadata={"data_key": "thermostat"}
    )
    schedule: dict[str, float]
    max_thermostat_temp: float = DEFAULT_MAX_THERMOSTAT_TEMP
    min_thermostat_temp: float = DEFAULT_MIN_THERMOSTAT_TEMP
    max_effective_thermostat_temp: float = DEFAULT_MAX_EFFECTIVE_THERMOSTAT_TEMP
    min_effective_thermostat_temp: float = DEFAULT_MIN_EFFECTIVE_THERMOSTAT_TEMP
    max_target_diff: float = DEFAULT_MAX_TARGET_DIFF
