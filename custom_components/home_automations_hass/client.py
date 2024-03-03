"""Client."""

import datetime
from logging import Logger

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import get_time_zone

from home_automations.models.status import Status


class Client:
    """Client."""

    def __init__(self, hass: HomeAssistant, logger: Logger, url: str) -> None:
        """Init."""

        self._hass = hass
        self._url = url
        self._logger = logger

    async def async_get_status(self) -> Status | None:
        """GET /status."""

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(10)
            ) as session, session.get(f"{self._url}/status") as response:
                if response.status != 200:
                    return None

                data = await response.json()
                last_state_changed_str: str = data["last_state_changed"]
                last_state_changed: datetime.datetime = datetime.datetime.fromisoformat(
                    last_state_changed_str
                )
                tzinfo = get_time_zone(self._hass.config.time_zone)
                last_state_changed = last_state_changed.replace(tzinfo=tzinfo)
                return Status(last_state_changed=last_state_changed)
        except TimeoutError:
            self._logger.error("Timeout")
            return None
