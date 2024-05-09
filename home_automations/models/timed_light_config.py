from dataclasses import dataclass, field


@dataclass
class TimedLightConfig:
    light_entities: list[str]
    light_on_entities: list[str] = field(default_factory=list)
    schedule_entity: str | None = None
    switch_entity: str | None = None
    on_elevation: float | None = None
    off_time: str | None = None
