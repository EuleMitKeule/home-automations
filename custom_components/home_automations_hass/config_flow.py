from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_URL
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .schemas import SCHEMA_CONFIG_FLOW_USER


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
