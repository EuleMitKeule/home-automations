from abc import ABC

from hass_client.models import Event, State

from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.helper.clock_events import ClockEvents
from home_automations.models.config import Config


class BaseModule(ClockEvents, ABC):
    client: Client
    state_changed_events: dict[str, list[callable]] = {}

    def __init__(self, config: Config, client: Client):
        self.client = client
        self.config = config

        Clock.register_module(self)

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

    def register_state_changed(self, method_callable: callable, entity_id: str):
        if entity_id not in self.state_changed_events:
            self.state_changed_events[entity_id] = []

        self.state_changed_events[entity_id].append(method_callable)
