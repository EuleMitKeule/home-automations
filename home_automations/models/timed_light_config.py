from dataclasses import dataclass


@dataclass
class TimedLightConfig:
    light_entities: list[str]
    light_on_entities: list[str]
    schedule_entity: str | None = None
    switch_entity: str | None = None
    on_elevation: float | None = None
    off_time: str | None = None
