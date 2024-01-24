from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import Client
from .const import DOMAIN
from .coordinator import Coordinator


class BaseEntity(CoordinatorEntity):
    def __init__(self, client: Client, coordinator: Coordinator):
        super().__init__(coordinator)

        self._client = client
        self._coordinator = coordinator
        self._attr_has_entity_name = True

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""

        return f"{DOMAIN}_{self._client._url}_{self.name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""

        return DeviceInfo(
            identifiers={(DOMAIN, self._client._url)},
            name="Home Automations",
            manufacturer="Home Automations",
            model="Home Automations",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self.schedule_update_ha_state()
