from dataclasses import dataclass, field
from datetime import time
from enum import StrEnum


class MotionLightStateType(StrEnum):
    ELEVATION = "elevation"
    TIME = "time"


@dataclass
class ElevationMotionLightState:
    elevation: float


@dataclass
class TimeMotionLightState:
    _time_from: str = field(metadata={"data_key": "from"})
    _time_to: str = field(metadata={"data_key": "to"})

    @property
    def time_from(self) -> time:
        return time.fromisoformat(self._time_from)

    @property
    def time_to(self) -> time:
        return time.fromisoformat(self._time_to)


@dataclass
class MotionLightState:
    scene: str


@dataclass
class ExtraMotionLightState(MotionLightState):
    elevation_state: ElevationMotionLightState | None = None
    time_state: TimeMotionLightState | None = None

    # check that either elevation_state or time_state is set
    def __post_init__(self):
        if self.elevation_state is None and self.time_state is None:
            raise ValueError("either elevation_state or time_state must be set")
        if self.elevation_state is not None and self.time_state is not None:
            raise ValueError("only one of elevation_state or time_state can be set")


@dataclass
class MotionLightConfig:
    name: str
    default_state: MotionLightState
    light_on_entities: list[str] = field(default_factory=list)
    light_off_entities: list[str] = field(default_factory=list)
    motion_entities: list[str] = field(default_factory=list)
    switch_entities: list[str] = field(default_factory=list)
    dimmer_ieees: list[str] = field(default_factory=list)
    states: list[ExtraMotionLightState] = field(default_factory=list)
    on_delay: float = 0
    off_delay: float = 0
