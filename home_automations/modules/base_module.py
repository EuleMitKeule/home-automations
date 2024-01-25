"""Base module for all modules."""

from abc import ABC
from typing import Any, Callable

from hass_client.models import Event, State

from home_automations.helper.clock_events import ClockEvents
from home_automations.models.config import Config
from home_automations.tools import Tools


class BaseModule(ClockEvents, ABC):
    def __init__(
        self,
        config: Config,
        tools: Tools,
    ):
        self.config: Config = config
        self.tools: Tools = tools
        self.state_changed_events: dict[str, list[Callable]] = {}
        self.zha_events: dict[str, list[Callable]] = {}

        self.tools.clock.register_module(self)

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
