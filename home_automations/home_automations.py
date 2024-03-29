import asyncio
import logging
from typing import Any, Callable

from fastapi import FastAPI
from hass_client.exceptions import (
    CannotConnect,
    ConnectionFailed,
    FailedCommand,
    NotConnected,
    NotFoundError,
)
from hass_client.models import Event

from home_automations.helper.client import HomeAssistantClient
from home_automations.helper.clock import Clock
from home_automations.helper.day_state import DayStateResolver
from home_automations.home_automations_api import HomeAutomationsApi
from home_automations.models.config import Config
from home_automations.models.exceptions import NotFoundAgainError, ServiceTimeoutError
from home_automations.modules.base_module import BaseModule
from home_automations.modules.dimmer_module import DimmerModule
from home_automations.modules.dummy_module import DummyModule
from home_automations.modules.motion_light_module import MotionLightModule
from home_automations.modules.sensor_notify_module import SensorNotifyModule
from home_automations.modules.thermostat_module import ThermostatModule
from home_automations.modules.tibber_module import TibberModule
from home_automations.modules.timed_light_module import TimedLightModule
from home_automations.tools import Tools


class HomeAutomations:
    def __init__(self, fastapi: FastAPI):
        """Initialize the HomeAutomations class."""

        self.fastapi = fastapi
        self.connection_task: asyncio.Task | None = None
        self.update_task: asyncio.Task | None = None
        self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()

        self.loop.set_exception_handler(self.handle_exception_in_loop)

        self.config: Config = fastapi.state.config

        client = HomeAssistantClient(self.config)
        clock = Clock(self.config)
        api = HomeAutomationsApi(fastapi)
        day_state = DayStateResolver(clock, client)
        self.tools = Tools(
            loop=self.loop,
            client=client,
            clock=clock,
            api=api,
            day_state_resolver=day_state,
        )

        self.tools.client.register_on_connection(self.on_connection)

        self.modules: list[BaseModule] = (
            [
                ThermostatModule(
                    self.config,
                    self.tools,
                    climate_config,
                    thermostat_config,
                )
                for climate_config in self.config.climate_configs
                for thermostat_config in climate_config.thermostat_configs
            ]
            + [
                DimmerModule(self.config, self.tools, dimmer_config)
                for dimmer_config in self.config.dimmer_configs
            ]
            + [
                TimedLightModule(self.config, self.tools, timed_light_config)
                for timed_light_config in self.config.timed_light_configs
            ]
            + [
                TibberModule(self.config, self.tools),
                DummyModule(self.config, self.tools),
            ]
            + [
                MotionLightModule(self.config, self.tools, motion_light_config)
                for motion_light_config in self.config.motion_light_configs
            ]
            + [
                SensorNotifyModule(self.config, self.tools, sensor_notify_config)
                for sensor_notify_config in self.config.sensor_notify_configs
            ]
        )

    async def start(self):
        """Handle application start."""

        await self.tools.client.connect()

    async def on_connection(self):
        async def on_event(event: Event):
            await self.handle_exception_in_func(self.on_event, event)

        await self.handle_exception_in_func(
            self.tools.client.subscribe_events,
            on_event,
        )

        if (
            self.update_task is None
            or self.update_task.done()
            or self.update_task.cancelled()
        ):
            self.update_task = self.loop.create_task(self.update())

    async def update(self):
        while True:
            await self.handle_exception_in_func(self.tools.clock.run)
            await asyncio.sleep(0.25)

    async def on_event(self, event: Event):
        """Handle an event from Home Assistant."""

        for module in self.modules:
            await module.on_event(event)

            if event.event_type == "state_changed":
                await module.on_state_changed(event)

            if event.event_type == "zha_event":
                await module.on_zha_event(event)

    def handle_exception_in_loop(
        self, loop: asyncio.AbstractEventLoop, context: dict[str, Any]
    ):
        """Handle an exception in the event loop."""

        exception = context.get("exception")

        if exception is None:
            return

        self.handle_exception(exception)

    async def handle_exception_in_func(self, func: Callable, *args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as ex:
            self.handle_exception(ex)

    def handle_exception(self, exception: Exception):
        """Handle an exception in the event loop."""

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
                if (
                    self.update_task is not None
                    and not self.update_task.done()
                    and not self.update_task.cancelled()
                ):
                    self.update_task.cancel()

                if self.connection_task is not None and not self.connection_task.done():
                    return
                self.connection_task = self.loop.create_task(
                    self.tools.client.connect()
                )
            case Exception():
                logging.exception(exception)
