"""Base module for all modules."""

from abc import ABC
from datetime import datetime, timedelta
from typing import Any, Callable

from hass_client.models import Event, State

from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.helper.clock_events import ClockEvents
from home_automations.home_automations_api import HomeAutomationsApi
from home_automations.models.config import Config


class BaseModule(ClockEvents, ABC):
    config: Config
    client: Client
    api: HomeAutomationsApi
    state_changed_events: dict[str, list[Callable]]
    zha_events: dict[str, list[Callable]]
    scheduled_tasks: dict[str, tuple[Callable, timedelta, datetime]]

    def __init__(self, config: Config, client: Client, api: HomeAutomationsApi):
        self.client = client
        self.config = config
        self.api = api
        self.state_changed_events = {}
        self.zha_events = {}
        self.scheduled_tasks = {}

        Clock.register_module(self)

    def _register_event_callback(
        self, key: Any, method_callable: Callable, event_dict: dict[Any, list[Callable]]
    ):
        if key not in event_dict:
            event_dict[key] = []

        event_dict[key].append(method_callable)

    def _get_event_callbacks(
        self, key: Any, event_dict: dict[Any, list[Callable]]
    ) -> list[Callable]:
        if key not in event_dict:
            return []

        return event_dict[key]

    async def on_event(self, event: Event):
        pass

    async def on_state_changed(self, event: Event):
        if event.data["entity_id"] not in self.state_changed_events:
            return

        if "old_state" not in event.data or "new_state" not in event.data:
            return

        if event.data["old_state"] is None or event.data["new_state"] is None:
            return

        old_state = State(**event.data["old_state"])
        new_state = State(**event.data["new_state"])

        for method_callable in self.state_changed_events[event.data["entity_id"]]:
            await method_callable(event, old_state, new_state)

    async def on_zha_event(self, event: Event):
        if "device_ieee" not in event.data:
            return

        device_ieee = event.data["device_ieee"]

        if device_ieee not in self.zha_events:
            return

        for method_callable in self.zha_events[device_ieee]:
            await method_callable(event, device_ieee)

    def register_state_changed(self, method_callable: Callable, entity_id: str):
        self._register_event_callback(
            entity_id, method_callable, self.state_changed_events
        )

    def register_zha_event(self, method_callable: Callable, device_ieee: str):
        self._register_event_callback(device_ieee, method_callable, self.zha_events)
