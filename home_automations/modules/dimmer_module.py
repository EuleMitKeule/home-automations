from hass_client.models import Event

from home_automations.helper.client import Client
from home_automations.home_automations_api import HomeAutomationsApi
from home_automations.models.config import Config
from home_automations.models.dimmer_config import DimmerConfig
from home_automations.modules.base_module import BaseModule


class DimmerModule(BaseModule):
    dimmer_config: DimmerConfig

    def __init__(
        self,
        config: Config,
        client: Client,
        api: HomeAutomationsApi,
        dimmer_config: DimmerConfig,
    ):
        super().__init__(config, client, api)

        self.dimmer_config = dimmer_config

        self.register_zha_event(self.on_dimmer_event, self.dimmer_config.device_ieee)

    async def on_off(self):
        pass

    async def on_on(self):
        for light_entity in self.dimmer_config.light_entities:
            await self.client.call_service(
                "light",
                "turn_on",
                service_data={
                    "brightness_pct": 100,
                },
                target={
                    "entity_id": light_entity,
                },
            )

    async def on_press(self):
        pass

    async def on_hold(self):
        pass

    async def on_release(self):
        pass

    async def on_dimmer_event(self, event: Event, device_ieee: str):
        if "command" not in event.data:
            return

        command = event.data["command"]

        match command:
            case "off":
                await self.on_off()
            case "on":
                await self.on_on()
            case "press":
                await self.on_press()
            case "hold":
                await self.on_hold()
            case "release":
                await self.on_release()
