from dataclasses import dataclass

from home_automations.const import DEFAULT_MAX_TARGET_TEMP, DEFAULT_MIN_TARGET_TEMP


@dataclass
class ThermostatConfig:
    name: str
    entity_id: str
    schedule: dict[str, float]
    windows: list[str]
    switches: list[str]
    temperature_sensor: str | None
    max_target_temp: float = DEFAULT_MAX_TARGET_TEMP
    min_target_temp: float = DEFAULT_MIN_TARGET_TEMP
