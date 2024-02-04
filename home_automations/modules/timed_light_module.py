import logging

from hass_client.models import Event, State

from home_automations.models.config import Config
from home_automations.models.timed_light_config import TimedLightConfig
from home_automations.modules.base_module import BaseModule
from home_automations.tools import Tools


class TimedLightModule(BaseModule):
    timed_light_config: TimedLightConfig

    def __init__(
        self,
        config: Config,
        tools: Tools,
        timed_light_config: TimedLightConfig,
    ):
        super().__init__(config, tools)

        self.timed_light_config = timed_light_config

        self.register_state_changed(
            self.on_schedule_changed, self.timed_light_config.schedule_entity
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
