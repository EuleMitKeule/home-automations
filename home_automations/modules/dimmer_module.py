from hass_client.models import Event

from home_automations.helper.client import Client
from home_automations.models.config import Config
from home_automations.models.dimmer_config import DimmerConfig
from home_automations.modules.base_module import BaseModule


class DimmerModule(BaseModule):
    dimmer_config: DimmerConfig

    def __init__(self, config: Config, client: Client, dimmer_config: DimmerConfig):
        super().__init__(config, client)

        self.dimmer_config = dimmer_config

        self.register_zha_event(self.on_dimmer_event, self.dimmer_config.device_ieee)

    async def on_dimmer_event(self, event: Event):
        pass
