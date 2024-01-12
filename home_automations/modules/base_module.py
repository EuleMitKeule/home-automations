from abc import ABC
from typing import Any

from hass_client.models import Event, State

from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.helper.clock_events import ClockEvents
from home_automations.models.config import Config


class BaseModule(ClockEvents, ABC):
    client: Client
    state_changed_events: dict[str, list[callable]]
    zha_events: dict[str, list[callable]]

    def __init__(self, config: Config, client: Client):
        self.client = client
        self.config = config
        self.state_changed_events = {}
        self.zha_events = {}

        Clock.register_module(self)

    def _register_event_callback(
        self, key: Any, method_callable: callable, event_dict: dict[Any, list[callable]]
    ):
        if key not in event_dict:
            event_dict[key] = []

        event_dict[key].append(method_callable)

    def _get_event_callbacks(
        self, key: Any, event_dict: dict[Any, list[callable]]
    ) -> list[callable]:
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
        pass

    def register_state_changed(self, method_callable: callable, entity_id: str):
        self._register_event_callback(
            entity_id, method_callable, self.state_changed_events
        )

    def register_zha_event(self, method_callable: callable, device_ieee: str):
        self._register_event_callback(device_ieee, method_callable, self.zha_events)
