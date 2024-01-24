import voluptuous as vol
from homeassistant.const import CONF_URL

SCHEMA_CONFIG_FLOW_USER = vol.Schema(
    {
        vol.Required(CONF_URL): str,
    }
)
