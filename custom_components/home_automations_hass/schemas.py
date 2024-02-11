import voluptuous as vol
from homeassistant.const import CONF_URL

from custom_components.home_automations_hass.const import (
    CONF_WASHING_MACHINE_MAC,
    CONF_WASHING_MACHINE_MANUFACTURER,
    CONF_WASHING_MACHINE_MODEL,
    CONF_WASHING_MACHINE_SHELLY_ENTITY_ID,
)

SCHEMA_CONFIG_FLOW_USER = vol.Schema(
    {
        vol.Required(CONF_URL): str,
    }
)

SCHEMA_OPTIONS_FLOW_USER = vol.Schema(
    {
        vol.Required(CONF_WASHING_MACHINE_SHELLY_ENTITY_ID, default=""): str,
        vol.Required(CONF_WASHING_MACHINE_MAC, default=""): str,
        vol.Required(CONF_WASHING_MACHINE_MANUFACTURER, default=""): str,
        vol.Required(CONF_WASHING_MACHINE_MODEL, default=""): str,
    }
)
