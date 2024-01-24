"""Client."""

from logging import Logger

import aiohttp
from home_automations.models.status import Status


class Client:
    """Client."""

    def __init__(self, logger: Logger, url: str) -> None:
        """Init."""

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
                return Status(**data)
        except TimeoutError:
            self._logger.error("Timeout")
            return None
