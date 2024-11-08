from abc import ABC
from datetime import time

from home_automations.helper.client import HomeAssistantClient
from home_automations.helper.clock import Clock
from home_automations.models.motion_light_config import MotionLightConfig


class DayState(ABC):
    """Abstract class for day state."""

    def __init__(self, scene: str) -> None:
        self._scene = scene

    @property
    async def is_fulfilled(self) -> bool | None:
        """Return whether the day state is fulfilled."""

        raise NotImplementedError

    @property
    def scene(self) -> str:
        """Return the name of the day state."""

        return self._scene.lower()

    @property
    def sort_key(self) -> float:
        """Return the sort key of the day state."""

        raise NotImplementedError


class DefaultDayState(DayState):
    """Class for default day state."""

    @property
    async def is_fulfilled(self) -> bool | None:
        return True

    @property
    def sort_key(self) -> float:
        return float("inf")


class ElevationDayState(DayState):
    """Class for elevation day state."""

    def __init__(
        self, client: HomeAssistantClient, scene: str, elevation: float
    ) -> None:
        super().__init__(scene)
        self._client = client
        self._elevation = elevation

    @property
    async def _sun_elevation(self) -> float | None:
        result = await self._client.get_attribute("sun.sun", attribute="elevation")

        try:
            return float(result)
        except (ValueError, TypeError):
            return None

    @property
    async def is_fulfilled(self) -> bool | None:
        elevation = await self._sun_elevation

        if elevation is None:
            return None

        return elevation < self._elevation

    @property
    def sort_key(self) -> float:
        return self._elevation


class TimeDayState(DayState):
    """Class for time day state."""

    def __init__(
        self, clock: Clock, scene: str, from_time: time, to_time: time
    ) -> None:
        super().__init__(scene)
        self._clock = clock
        self._from_time = from_time
        self._to_time = to_time

    @property
    async def is_fulfilled(self) -> bool | None:
        now = self._clock.current_time()

        if self._from_time <= self._to_time:
            return self._from_time <= now <= self._to_time
        else:
            return now >= self._from_time or now <= self._to_time

    @property
    def sort_key(self) -> float:
        return self._from_time.hour + self._from_time.minute / 60


class DayStateResolver:
    def __init__(self, clock: Clock, client: HomeAssistantClient):
        self.client = client

    async def resolve(self, motion_light_config: MotionLightConfig) -> str:
        default_day_state = DefaultDayState(motion_light_config.default_state.scene)
        elevation_day_states = sorted(
            [
                ElevationDayState(
                    self.client, state.scene, state.elevation_state.elevation
                )
                for state in motion_light_config.states
                if state.elevation_state is not None
            ],
            key=lambda state: state.sort_key,
        )
        time_day_states = sorted(
            [
                TimeDayState(
                    Clock(self.client.config),
                    state.scene,
                    state.time_state.time_from,
                    state.time_state.time_to,
                )
                for state in motion_light_config.states
                if state.time_state is not None
            ],
            key=lambda state: state.sort_key,
        )

        for time_state in time_day_states:
            if await time_state.is_fulfilled:
                return time_state.scene

        for elevation_state in elevation_day_states:
            if await elevation_state.is_fulfilled:
                return elevation_state.scene

        return default_day_state.scene
