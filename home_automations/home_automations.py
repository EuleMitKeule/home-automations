import asyncio
import logging
from typing import Any, Callable

from hass_client.exceptions import (
    CannotConnect,
    ConnectionFailed,
    FailedCommand,
    NotConnected,
    NotFoundError,
)
from hass_client.models import Event

from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.home_automations_api import HomeAutomationsApi
from home_automations.models.config import Config
from home_automations.models.exceptions import NotFoundAgainError, ServiceTimeoutError
from home_automations.modules.base_module import BaseModule
from home_automations.modules.dimmer_module import DimmerModule
from home_automations.modules.dummy_module import DummyModule
from home_automations.modules.thermostat_module import ThermostatModule
from home_automations.modules.tibber_module import TibberModule


class HomeAutomations:
    config: Config
    client: Client
    api: HomeAutomationsApi
    loop: asyncio.AbstractEventLoop
    modules: list[BaseModule]
    connection_task: asyncio.Task | None

    def __init__(self, config: Config, client: Client, api: HomeAutomationsApi):
        """Initialize the HomeAutomations class."""

        self.config = config
        self.client = client
        self.api = api
        self.modules = [
            ThermostatModule(config, client, api, climate_config, thermostat_config)
            for climate_config in config.climate_configs
            for thermostat_config in climate_config.thermostat_configs
        ]
        self.modules += [
            DimmerModule(config, client, api, dimmer_config)
            for dimmer_config in config.dimmer_configs
        ]
        self.modules += [TibberModule(config, client, api)]
        self.modules += [DummyModule(config, client, api)]
        self.loop = asyncio.get_running_loop()
        self.loop.set_exception_handler(self.handle_exception)
        self.connection_task = None
        self.client.register_on_connection(self.on_connection)

    async def run(self):
        await self.on_connection()

        self.update_task = self.loop.create_task(self.update())
        await self.update_task

    async def on_connection(self):
        async def on_event(event: Event):
            await self.handle_errors(self.on_event, event)

        await self.handle_errors(
            self.client.subscribe_events,
            on_event,
        )

    async def update(self):
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

    def handle_exception(
        self, loop: asyncio.AbstractEventLoop, context: dict[str, Any]
    ):
        """Handle an exception in the event loop."""

        exception = context.get("exception")

        match exception:
            case NotFoundError():
                logging.error(exception)
            case NotFoundAgainError():
                logging.debug(exception)
            case ServiceTimeoutError():
                logging.debug(exception)
            case asyncio.CancelledError():
                logging.error("Operation was cancelled")
            case FailedCommand():
                logging.error(exception)
            case NotConnected() | CannotConnect() | ConnectionFailed():
                if self.connection_task is not None and not self.connection_task.done():
                    return
                self.connection_task = self.loop.create_task(self.client.connect())
            case Exception():
                logging.exception(exception)

    async def handle_errors(self, func: Callable, *args, **kwargs):
        try:
            await func(*args, **kwargs)
        except NotFoundError as e:
            logging.error(e)
        except NotFoundAgainError as e:
            logging.debug(e)
        except ServiceTimeoutError as e:
            logging.debug(e)
        except asyncio.CancelledError:
            logging.error("Operation was cancelled")
        except FailedCommand as e:
            logging.error(e)
        except (
            NotConnected,
            CannotConnect,
            ConnectionFailed,
        ):
            if self.connection_task is not None and not self.connection_task.done():
                return
            self.connection_task = self.loop.create_task(self.client.connect())
        except Exception as e:
            logging.exception(e)
