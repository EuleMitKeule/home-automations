import asyncio
import logging

from dependency_injector.wiring import inject
from hass_client import HomeAssistantClient
from hass_client.exceptions import (
    AuthenticationFailed,
    CannotConnect,
    ConnectionFailed,
    NotConnected,
    NotFoundError,
)
from hass_client.models import Event

from home_automations.helper.clock import Clock
from home_automations.models.config import Config
from home_automations.modules.base_module import BaseModule
from home_automations.modules.thermostat_module import ThermostatModule


class HomeAutomations:
    config: Config
    hass_client: HomeAssistantClient
    modules: list[BaseModule]

    @inject
    def __init__(self, config: Config):
        """Initialize the HomeAutomations class."""

        self.config = config
        self.hass_client = HomeAssistantClient(
            self.config.homeassistant.url, self.config.homeassistant.token
        )
        self.modules = [
            ThermostatModule(self.hass_client, config, thermostat_config)
            for thermostat_config in config.thermostats
        ]

    async def run(self):
        """Run the HomeAutomations class."""

        while True:
            try:
                async with self.hass_client:
                    loop = asyncio.get_event_loop()
                    loop.create_task(Clock.run())
                    await self.hass_client.subscribe_events(self.on_event)
                    await asyncio.sleep(1000)
            except (NotConnected, CannotConnect, ConnectionFailed):
                logging.error("Not connected to Home Assistant, retrying in 5 seconds")
                await asyncio.sleep(5)
            except AuthenticationFailed:
                logging.error("Authentication failed")
                break
            except NotFoundError as e:
                logging.error(e)

    async def on_event(self, event: Event):
        """Handle an event from Home Assistant."""

        for module in self.modules:
            await module.on_event(event)

            if event.event_type == "state_changed":
                await module.on_state_changed(event)
