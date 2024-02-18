from datetime import datetime

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base_entity import BaseEntity
from .client import Client
from .const import (
    CONF_DRYER_MAC,
    CONF_DRYER_MANUFACTURER,
    CONF_DRYER_MODEL,
    CONF_DRYER_SHELLY_ENTITY_ID,
    CONF_WASHING_MACHINE_MAC,
    CONF_WASHING_MACHINE_MANUFACTURER,
    CONF_WASHING_MACHINE_MODEL,
    CONF_WASHING_MACHINE_SHELLY_ENTITY_ID,
    DOMAIN,
)
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
        RunningSensor(config_entry, client, coordinator),
        StateMonitoringSensor(config_entry, client, coordinator),
        WashingMachineSensor(config_entry, client, coordinator),
        DryerSensor(config_entry, client, coordinator),
    ]

    async_add_entities(entities_to_add)


class RunningSensor(BaseEntity, BinarySensorEntity):
    """Running Sensor."""

    def __init__(self, entry: ConfigEntry, client: Client, coordinator: Coordinator):
        super().__init__(entry, client, coordinator)

        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_name = "Running"
        self._attr_unique_id = f"{DOMAIN}_{self._client._url}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""

        return self._coordinator.status is not None


class StateMonitoringSensor(BaseEntity, BinarySensorEntity):
    """State Monitoring Sensor."""

    def __init__(self, entry: ConfigEntry, client: Client, coordinator: Coordinator):
        super().__init__(entry, client, coordinator)

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


class WashingMachineSensor(BaseEntity, BinarySensorEntity):
    """Running Sensor."""

    def __init__(self, entry: ConfigEntry, client: Client, coordinator: Coordinator):
        super().__init__(entry, client, coordinator)

        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_name = "Waschmaschine"
        self._attr_unique_id = "waschmaschine"

        mac_address: str = self._config_entry.options.get(CONF_WASHING_MACHINE_MAC)
        manufacturer: str = self._config_entry.options.get(
            CONF_WASHING_MACHINE_MANUFACTURER
        )
        model: str = self._config_entry.options.get(CONF_WASHING_MACHINE_MODEL)

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, mac_address)},
            manufacturer=manufacturer,
            model=model,
            name="Waschmaschine",
        )

    @property
    def state(self) -> str:
        """Return the state of the sensor."""

        shelly_entity_id: str = self._config_entry.options.get(
            CONF_WASHING_MACHINE_SHELLY_ENTITY_ID
        )

        state = self.hass.states.get(shelly_entity_id)

        if state == "unavailable" or state is None:
            return "off"

        try:
            power = float(state.state)
        except ValueError:
            raise HomeAssistantError(f"Invalid power value: {state.state}")

        if power > 0:
            return "on"

        return "off"


class DryerSensor(BaseEntity, BinarySensorEntity):
    """Running Sensor."""

    def __init__(self, entry: ConfigEntry, client: Client, coordinator: Coordinator):
        super().__init__(entry, client, coordinator)

        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_name = "Trockner"
        self._attr_unique_id = "trockner"

        mac_address: str = self._config_entry.options.get(CONF_DRYER_MAC)
        manufacturer: str = self._config_entry.options.get(CONF_DRYER_MANUFACTURER)
        model: str = self._config_entry.options.get(CONF_DRYER_MODEL)

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, mac_address)},
            manufacturer=manufacturer,
            model=model,
            name="Trockner",
        )

    @property
    def state(self) -> str:
        """Return the state of the sensor."""

        shelly_entity_id: str = self._config_entry.options.get(
            CONF_DRYER_SHELLY_ENTITY_ID
        )

        state = self.hass.states.get(shelly_entity_id)

        if state == "unavailable" or state is None:
            return "off"

        try:
            power = float(state.state)
        except ValueError:
            raise HomeAssistantError(f"Invalid power value: {state.state}")

        if power > 0:
            return "on"

        return "off"
