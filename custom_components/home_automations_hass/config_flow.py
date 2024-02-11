from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_URL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_WASHING_MACHINE_MAC,
    CONF_WASHING_MACHINE_MANUFACTURER,
    CONF_WASHING_MACHINE_MODEL,
    CONF_WASHING_MACHINE_SHELLY_ENTITY_ID,
    DOMAIN,
)


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
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_URL): str,
                    }
                ),
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
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_WASHING_MACHINE_SHELLY_ENTITY_ID,
                        default=self.config_entry.options.get(
                            CONF_WASHING_MACHINE_SHELLY_ENTITY_ID, ""
                        ),
                    ): str,
                    vol.Required(
                        CONF_WASHING_MACHINE_MAC,
                        default=self.config_entry.options.get(
                            CONF_WASHING_MACHINE_MAC, ""
                        ),
                    ): str,
                    vol.Required(
                        CONF_WASHING_MACHINE_MANUFACTURER,
                        default=self.config_entry.options.get(
                            CONF_WASHING_MACHINE_MANUFACTURER, ""
                        ),
                    ): str,
                    vol.Required(
                        CONF_WASHING_MACHINE_MODEL,
                        default=self.config_entry.options.get(
                            CONF_WASHING_MACHINE_MODEL, ""
                        ),
                    ): str,
                }
            ),
        )
