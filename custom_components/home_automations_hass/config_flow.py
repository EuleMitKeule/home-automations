from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .schemas import SCHEMA_CONFIG_FLOW_USER, SCHEMA_OPTIONS_FLOW_USER


class HomeAutomationsConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Config Flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""

        errors: dict[str, str] | None = {}
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=SCHEMA_CONFIG_FLOW_USER,
                errors=errors,
            )

        url = user_input[CONF_URL]

        await self.async_set_unique_id(url)
        self._abort_if_unique_id_configured(updates=user_input)
        return self.async_create_entry(title="Home Automations", data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""

        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Options flow for eQ-3 Bluetooth Smart thermostats."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=SCHEMA_OPTIONS_FLOW_USER,
        )
