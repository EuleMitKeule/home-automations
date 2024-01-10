import asyncio
import logging

from dependency_injector.wiring import inject
from hass_client.exceptions import (
    AuthenticationFailed,
    CannotConnect,
    ConnectionFailed,
    NotConnected,
    NotFoundError,
)
from hass_client.models import Event

from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.models.config import Config
from home_automations.models.exceptions import NotFoundAgainError
from home_automations.modules.base_module import BaseModule
from home_automations.modules.thermostat_module import ThermostatModule
from home_automations.modules.tibber_module import TibberModule


class HomeAutomations:
    config: Config
    client: Client
    loop: asyncio.AbstractEventLoop
    modules: list[BaseModule]

    @inject
    def __init__(self, config: Config, client: Client):
        """Initialize the HomeAutomations class."""

        self.config = config
        self.client = client
        self.modules = [
            ThermostatModule(config, client, thermostat_config)
            for thermostat_config in config.thermostats
        ]
        self.modules += [TibberModule(config, client)]
        self.loop = asyncio.get_running_loop()

    async def run(self):
        """Run the HomeAutomations class."""

        while True:
            try:
                try:
                    await self.client.subscribe_events(self.on_event)
                except (NotConnected, CannotConnect, ConnectionFailed):
                    logging.error(
                        "Not connected to Home Assistant, retrying in 5 seconds"
                    )
                    await asyncio.sleep(5)
                    continue
                except AuthenticationFailed:
                    logging.error("Authentication failed")
                    break
                await Clock.run()
                await asyncio.sleep(0.25)
            except NotFoundError as e:
                logging.error(e)
            except NotFoundAgainError:
                pass

    async def on_event(self, event: Event):
        """Handle an event from Home Assistant."""

        for module in self.modules:
            await module.on_event(event)

            if event.event_type == "state_changed":
                await module.on_state_changed(event)

            if event.event_type == "zha_event":
                await module.on_zha_event(event)
