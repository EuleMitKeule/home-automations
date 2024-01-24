from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base_entity import BaseEntity
from .client import Client
from .const import DOMAIN
from .coordinator import Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Called when an entry is setup."""

    client = hass.data[config_entry.entry_id]["client"]
    coordinator = hass.data[config_entry.entry_id]["coordinator"]

    entities_to_add: list[Entity] = [
        RunningSensor(client, coordinator),
        StateMonitoringSensor(client, coordinator),
    ]

    async_add_entities(entities_to_add)


class RunningSensor(BaseEntity, BinarySensorEntity):
    """Running Sensor."""

    def __init__(self, client: Client, coordinator: Coordinator):
        super().__init__(client, coordinator)

        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_name = "Running"
        self._attr_unique_id = f"{DOMAIN}_{self._client._url}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""

        return self._coordinator.status is not None


class StateMonitoringSensor(BaseEntity, BinarySensorEntity):
    """State Monitoring Sensor."""

    def __init__(self, client: Client, coordinator: Coordinator):
        super().__init__(client, coordinator)

        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_name = "State Monitoring"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""

        if self._coordinator.status is None:
            return False

        last_state_changed = self._coordinator.status.last_state_changed
        now = datetime.now()

        seconds_since_last_state_change = (now - last_state_changed).total_seconds()

        return seconds_since_last_state_change < 60
