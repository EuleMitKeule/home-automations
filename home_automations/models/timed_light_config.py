from dataclasses import dataclass


@dataclass
class TimedLightConfig:
    light_entities: list[str]
    schedule_entity: str
    switch_entity: str | None = None
