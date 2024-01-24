from datetime import timedelta
from logging import Logger

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from home_automations.models.status import Status

from .client import Client


class Coordinator(DataUpdateCoordinator):
    """Coordinator."""

    def __init__(self, hass: HomeAssistant, logger: Logger, client: Client):
        super().__init__(
            hass,
            logger,
            update_interval=timedelta(seconds=10),
            update_method=self.update,
            name="Home Automations",
        )

        self._client = client
        self._status: Status | None = None

    @property
    def status(self) -> Status | None:
        """Return status."""

        return self._status

    async def update(self) -> None:
        """Update data."""

        self._status = await self._client.async_get_status()
