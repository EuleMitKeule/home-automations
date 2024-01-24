from datetime import datetime, timedelta

from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.home_automations_api import HomeAutomationsApi
from home_automations.models.config import Config
from home_automations.modules.base_module import BaseModule


class DummyModule(BaseModule):
    def __init__(self, config: Config, client: Client, api: HomeAutomationsApi):
        super().__init__(config, client, api)

        self.register_state_changed(
            self.on_dummy_state_changed, "switch.home_automations_dummy"
        )

        Clock.register_task(self.switch_dummy, timedelta(seconds=5))

    async def switch_dummy(self) -> None:
        await self.client.call_service(
            "switch",
            "toggle",
            target={
                "entity_id": "switch.home_automations_dummy",
            },
        )

    async def on_dummy_state_changed(self, event, old_state, new_state) -> None:
        self.api._last_state_changed = datetime.now()
