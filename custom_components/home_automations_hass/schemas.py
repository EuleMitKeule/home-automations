import voluptuous as vol
from homeassistant.const import CONF_URL
from homeassistant.helpers import config_validation as cv

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
        vol.Required(CONF_WASHING_MACHINE_SHELLY_ENTITY_ID, default=""): cv.entity_id,
        vol.Required(CONF_WASHING_MACHINE_MAC, default=""): cv.string,
        vol.Required(CONF_WASHING_MACHINE_MANUFACTURER, default=""): cv.string,
        vol.Required(CONF_WASHING_MACHINE_MODEL, default=""): cv.string,
    }
)
