import asyncio
import logging
from typing import Coroutine

from dependency_injector.wiring import inject
from hass_client.exceptions import (
    CannotConnect,
    ConnectionFailed,
    NotConnected,
    NotFoundError,
)
from hass_client.models import Event

from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.models.config import Config
from home_automations.models.exceptions import NotFoundAgainError, ServiceTimeoutError
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
            ThermostatModule(config, client, climate_config, thermostat_config)
            for climate_config in config.climate_configs
            for thermostat_config in climate_config.thermostat_configs
        ]
        self.modules += [TibberModule(config, client)]
        self.loop = asyncio.get_running_loop()

    async def run(self):
        """Run the HomeAutomations class."""

        async def on_event(event: Event):
            await self.handle_errors(self.on_event, event)

        await self.handle_errors(
            self.client.subscribe_events,
            on_event,
        )

        while True:
            await self.handle_errors(Clock.run)
            await asyncio.sleep(0.25)

    async def on_event(self, event: Event):
        """Handle an event from Home Assistant."""

        for module in self.modules:
            await module.on_event(event)

            if event.event_type == "state_changed":
                await module.on_state_changed(event)

            if event.event_type == "zha_event":
                await module.on_zha_event(event)

    async def handle_errors(self, func: Coroutine, *args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except NotFoundError as e:
            logging.error(e)
        except NotFoundAgainError as e:
            logging.debug(e)
        except ServiceTimeoutError as e:
            logging.debug(e)
        except asyncio.CancelledError:
            logging.error("Operation was cancelled")
        except (
            NotConnected,
            CannotConnect,
            ConnectionFailed,
        ):
            await self.client.connect()
        except Exception as e:
            logging.exception(e)
