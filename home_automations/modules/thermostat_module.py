import logging

from hass_client.client import HomeAssistantClient
from hass_client.models import Event, State

from home_automations.const import ThermostatState
from home_automations.helper.clock import Clock
from home_automations.models.config import Config
from home_automations.models.thermostat_config import ThermostatConfig
from home_automations.modules.base_module import BaseModule


class ThermostatModule(BaseModule):
    """Module for controlling a thermostat."""

    def __init__(
        self,
        hass_client: HomeAssistantClient,
        config: Config,
        thermostat_config: ThermostatConfig,
    ):
        super().__init__(hass_client, config)

        self.thermostat_config = thermostat_config

        for window in self.thermostat_config.windows:
            self.register_state_changed(self.on_window_changed, window)

    @property
    async def is_window_open(self) -> bool:
        """Return whether one of the windows is open."""

        for window in self.thermostat_config.windows:
            state = await self.hass_client.get_state(window)

            if state.state == "on":
                return True

        return False

    @property
    async def is_switch_off(self) -> bool:
        """Return whether any of the switches are off."""

        for switch in self.thermostat_config.switches:
            state = await self.hass_client.get_state(switch)

            if state.state == "off":
                return True

        return False

    @property
    async def should_set_state(self) -> bool:
        """Return whether the thermostat should be turned on."""

        if await self.is_switch_off:
            return False

        return True

    @property
    async def should_set_temp(self) -> bool:
        """Return whether the thermostat should be set."""

        if await self.is_switch_off:
            return False

        has_target_temp = await self.current_temp == self.target_temp
        is_target_off = await self.target_state == ThermostatState.OFF
        is_unavailable = await self.current_state == ThermostatState.UNAVAILABLE

        if not has_target_temp and not is_target_off and not is_unavailable:
            return True

        return False

    @property
    async def target_state(self) -> ThermostatState:
        """Return the target state for the current time."""

        if await self.is_window_open:
            return ThermostatState.OFF

        return ThermostatState.HEAT

    @property
    def target_temp(self) -> float:
        """Return the target temperature for the current time."""

        return Clock.resolve_schedule(self.thermostat_config.schedule)

    @property
    async def current_state(self) -> ThermostatState:
        """Return the current state."""

        state = await self.hass_client.get_state(self.thermostat_config.entity_id)

        return state.state

    @property
    async def current_temp(self) -> float | None:
        """Return the current temperature."""

        state = await self.hass_client.get_state(self.thermostat_config.entity_id)

        if "temperature" in state.attributes:
            return state.attributes["temperature"]

        return None

    async def apply_state(self):
        """Apply the on/off state."""

        if not await self.should_set_state:
            return

        service = (
            "turn_off" if await self.target_state == ThermostatState.OFF else "turn_off"
        )

        logging.info(
            f"Turning {'off' if await self.target_state == ThermostatState.OFF else 'on'} {self.thermostat_config.entity_id}."
        )

        await self.hass_client.call_service(
            "climate",
            service,
            target={"entity_id": self.thermostat_config.entity_id},
        )

        if await self.target_state == ThermostatState.OFF:
            return

        await self.apply_target_temp()

    async def apply_target_temp(self):
        """Apply the target temperature."""

        if not await self.should_set_temp:
            return

        logging.info(
            f"Setting {self.thermostat_config.entity_id} to {self.target_temp}."
        )

        await self.hass_client.call_service(
            "climate",
            "set_temperature",
            service_data={"temperature": self.target_temp},
            target={"entity_id": self.thermostat_config.entity_id},
        )

    async def on_window_changed(self, event: Event, old_state: State, new_state: State):
        await self.apply_state()

    async def on_second_changed(self, second: int):
        await self.apply_target_temp()
