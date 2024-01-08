from dataclasses import dataclass


@dataclass
class ThermostatConfig:
    name: str
    entity_id: str
    limit_temp: float
    schedule: dict[str, float]
    windows: list[str]
    switches: list[str]
