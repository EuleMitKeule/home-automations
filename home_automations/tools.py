import asyncio
from dataclasses import dataclass

from home_automations.helper.client import HomeAssistantClient
from home_automations.helper.clock import Clock
from home_automations.helper.day_state import DayStateResolver
from home_automations.home_automations_api import HomeAutomationsApi


@dataclass
class Tools:
    loop: asyncio.AbstractEventLoop
    clock: Clock
    client: HomeAssistantClient
    api: HomeAutomationsApi
    day_state_resolver: DayStateResolver
