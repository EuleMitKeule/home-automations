import logging
from datetime import timedelta

from hass_client.models import Event, State

from home_automations.helper.clock_events import ClockEvents
from home_automations.models.config import Config
from home_automations.models.timed_light_config import TimedLightConfig
from home_automations.modules.base_module import BaseModule
from home_automations.tools import Tools


class TimedLightModule(BaseModule, ClockEvents):
    timed_light_config: TimedLightConfig

    def __init__(
        self,
        config: Config,
        tools: Tools,
        timed_light_config: TimedLightConfig,
    ):
        super().__init__(config, tools)

        self.timed_light_config = timed_light_config

        if self.timed_light_config.schedule_entity is not None:
            self.register_state_changed(
                self.on_schedule_changed, self.timed_light_config.schedule_entity
            )
        elif (
            self.timed_light_config.on_elevation is not None
            and self.timed_light_config.off_time is not None
        ):
            self.register_state_changed(
                self.on_elevation_changed, "sensor.sonne_solar_elevation"
            )

    async def on_off(self):
        if not await self.is_switch_on():
            return

        for light_entity in self.timed_light_config.light_entities:
            await self.tools.client.call_service(
                "light",
                "turn_off",
                target={
                    "entity_id": light_entity,
                },
            )

    async def on_on(self):
        if not await self.is_switch_on():
            return

        for light_entity in self.timed_light_config.light_entities:
            await self.tools.client.call_service(
                "light",
                "turn_on",
                target={
                    "entity_id": light_entity,
                },
            )

    async def is_switch_on(self) -> bool:
        if self.timed_light_config.switch_entity is None:
            return True

        state = await self.tools.client.get_state(self.timed_light_config.switch_entity)

        return state.state == "on"

    async def on_schedule_changed(
        self, event: Event, old_state: State, new_state: State
    ) -> None:
        logging.info(
            f"Schedule changed: {old_state.entity_id} {old_state.state} -> {new_state.state}"
        )

        if new_state.state == old_state.state:
            return

        if new_state.state == "on":
            await self.on_on()

        if new_state.state == "off":
            await self.on_off()

    async def on_elevation_changed(
        self, event: Event, old_state: State, new_state: State
    ) -> None:
        if self.timed_light_config.on_elevation is None:
            return

        if (
            float(old_state.state)
            > self.timed_light_config.on_elevation
            >= float(new_state.state)
        ):
            await self.on_on()

    async def on_minute_changed(self, minute: int):
        if self.timed_light_config.off_time is None:
            return

        current_datetime = self.tools.clock.current_datetime()

        if current_datetime.minute == 0:
            pass

        previous_time = current_datetime + timedelta(minutes=-1)
        off_datetime = self.tools.clock.parse_datetime(self.timed_light_config.off_time)

        if previous_time < off_datetime <= current_datetime:
            await self.on_off()
