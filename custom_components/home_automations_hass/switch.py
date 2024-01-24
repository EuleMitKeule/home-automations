from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base_entity import BaseEntity
from .client import Client
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
        DummySwitch(client, coordinator),
    ]

    async_add_entities(entities_to_add)


class DummySwitch(BaseEntity, SwitchEntity):
    """Dummy Switch."""

    def __init__(self, client: Client, coordinator: Coordinator):
        super().__init__(client, coordinator)

        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_name = "Dummy"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off."""
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self._attr_is_on
