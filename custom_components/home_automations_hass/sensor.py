"""Sensor platform for the Home Automation integration."""

from homeassistant.components.homekit import SensorDeviceClass
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base_entity import BaseEntity
from .client import Client
from .const import WashingMachineState
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
        WashingMachineSensor(client, coordinator),
    ]

    async_add_entities(entities_to_add)


class WashingMachineSensor(BaseEntity, SensorEntity):
    """Running Sensor."""

    def __init__(self, client: Client, coordinator: Coordinator):
        super().__init__(client, coordinator)

        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_name = "Waschmaschine"
        self._attr_unique_id = "waschmaschine"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, "08:f9:e0:4e:62:4e")},
            manufacturer="Bosch",
            model="WAN282V8",
            name="Waschmaschine",
        )

    @property
    def state(self) -> str:
        """Return the state of the sensor."""

        return WashingMachineState.OFF
