from datetime import datetime, timedelta

from hass_client.models import Event, State

from home_automations.models.config import Config
from home_automations.modules.base_module import BaseModule
from home_automations.tools import Tools


class DummyModule(BaseModule):
    def __init__(
        self,
        config: Config,
        tools: Tools,
    ):
        super().__init__(config, tools)

        self.register_state_changed(
            self.on_dummy_state_changed, "switch.home_automations_dummy"
        )

        self.tools.clock.register_task(self.switch_dummy, timedelta(seconds=5))

    async def switch_dummy(self) -> None:
        await self.tools.client.call_service(
            "switch",
            "toggle",
            target={
                "entity_id": "switch.home_automations_dummy",
            },
        )

    async def on_dummy_state_changed(
        self, event: Event, old_state: State, new_state: State
    ) -> None:
        self.tools.api._last_state_changed = datetime.now()
