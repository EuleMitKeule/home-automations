import logging

from colour import Color
from tibber import FatalHttpException, Tibber

from home_automations.common import scheduler
from home_automations.const import TibberLevel
from home_automations.helper.client import Client
from home_automations.models.config import Config
from home_automations.modules.base_module import BaseModule


class TibberModule(BaseModule):
    """Module for tibber related automations."""

    tibber: Tibber
    last_level: TibberLevel = TibberLevel.UNKNOWN

    def __init__(self, config: Config, client: Client):
        super().__init__(config, client)

        self.tibber = Tibber(
            access_token=config.tibber.token,
            user_agent="Home Automations",
        )

        scheduler.add_job(self.on_update, "interval", minutes=2)

    async def on_update(self):
        try:
            await self.tibber.update_info()

            home = self.tibber.get_home(self.config.tibber.home_id)

            await home.fetch_consumption_data()
            await home.update_info()
            await home.update_price_info()

            level_str = home.current_price_info["level"]
            level = TibberLevel(level_str)
            price = home.current_price_info["total"]

            if price <= 0:
                level = TibberLevel.FREE

            if level not in self.config.tibber.level_to_color:
                return

            color_hex = self.config.tibber.level_to_color[level]
            color = Color(color_hex)

            for entity_id in self.config.tibber.light_entities:
                await self.client.call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "entity_id": entity_id,
                        "brightness_pct": 100,
                        "rgb_color": [
                            color.get_red() * 255,
                            color.get_green() * 255,
                            color.get_blue() * 255,
                        ],
                    },
                )

            self.last_level = level
        except FatalHttpException as e:
            logging.error(e)
