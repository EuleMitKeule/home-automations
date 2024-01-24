from dataclasses import dataclass


@dataclass
class ThermostatConfig:
    climate_entity: str
    temperature_entity: str
    window_entities: list[str]
