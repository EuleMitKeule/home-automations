from hass_client.models import Event, State

from home_automations.helper.clock_events import ClockEvents
from home_automations.models.config import Config
from home_automations.models.light_replacement_config import LightReplacementConfig
from home_automations.modules.base_module import BaseModule
from home_automations.tools import Tools


class LightReplacementModule(BaseModule, ClockEvents):
    def __init__(
        self,
        config: Config,
        tools: Tools,
        light_replacement_config: LightReplacementConfig,
    ):
        super().__init__(config, tools)

        self.light_replacement_config: LightReplacementConfig = light_replacement_config

        self.register_state_changed(
            self.on_light_changed, light_replacement_config.light_entity
        )

    async def on_light_changed(
        self, event: Event, old_state: State, new_state: State
    ) -> None:
        if old_state.state != "on" or new_state.state != "off":
            return

        for condition in self.light_replacement_config.conditions:
            state = await self.tools.client.get_state(condition.entity)

            if state.state != condition.state:
                return

        await self.tools.client.call_service(
            "light",
            "turn_on",
            target={
                "entity_id": self.light_replacement_config.light_replacement_entity
            },
        )
