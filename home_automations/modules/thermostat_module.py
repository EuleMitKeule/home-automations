import datetime
import logging

from hass_client.models import Event, State

from home_automations.const import ThermostatState
from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.models.config import Config
from home_automations.models.thermostat_config import ThermostatConfig
from home_automations.modules.base_module import BaseModule


class ThermostatModule(BaseModule):
    """Module for controlling a thermostat."""

    def __init__(
        self,
        config: Config,
        client: Client,
        thermostat_config: ThermostatConfig,
    ):
        super().__init__(config, client)

        self.thermostat_config = thermostat_config

        for window in self.thermostat_config.windows:
            self.register_state_changed(self.on_window_changed, window)

    @property
    async def is_window_open(self) -> bool:
        """Return whether one of the windows is open."""

        is_open: bool = False

        for window in self.thermostat_config.windows:
            state = await self.client.get_state(window)

            if state.state == "on":
                is_open = True

        return is_open

    @property
    async def is_switch_off(self) -> bool:
        """Return whether any of the switches are off."""

        for switch in self.thermostat_config.switches:
            state = await self.client.get_state(switch)

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
    async def has_scheduled_temp(self) -> bool:
        """Return whether the thermostat has a scheduled temperature."""

        return await self.temp_difference <= 0.25

    @property
    async def should_set_temp(self) -> bool:
        """Return whether the thermostat should be set."""

        if await self.is_switch_off:
            return False

        has_target_temp = await self.target_temp == await self.current_temp_climate
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
    async def temp_difference(self) -> float | None:
        """Return the difference between the current and target temperature."""

        return abs(await self.scheduled_temp - await self.current_temp)

    @property
    async def scheduled_temp(self) -> float | None:
        """Return the scheduled temperature for the current time."""

        return Clock.resolve_schedule(self.thermostat_config.schedule)

    @property
    async def target_temp(self) -> float | None:
        """Return the target temperature for the current time."""

        if await self.has_scheduled_temp:
            return await self.scheduled_temp

        if await self.scheduled_temp > await self.current_temp:
            return self.thermostat_config.max_target_temp

        return self.thermostat_config.min_target_temp

    @property
    async def current_state(self) -> ThermostatState:
        """Return the current state."""

        state = await self.client.get_state(self.thermostat_config.entity_id)

        return state.state

    @property
    async def current_temp_sensor(self) -> float | None:
        state = await self.client.get_state(self.thermostat_config.temperature_sensor)

        return float(state.state)

    @property
    async def current_temp_climate(self) -> float | None:
        state = await self.client.get_state(self.thermostat_config.entity_id)

        if "temperature" not in state.attributes:
            return None

        return float(state.attributes["temperature"])

    @property
    async def current_temp(self) -> float | None:
        """Return the current temperature."""

        if self.thermostat_config.temperature_sensor is not None:
            return await self.current_temp_sensor

        return await self.current_temp_climate

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

        await self.client.call_service(
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

        await self.client.call_service(
            "climate",
            "set_temperature",
            service_data={"temperature": await self.target_temp},
            target={"entity_id": self.thermostat_config.entity_id},
            timeout=datetime.timedelta(minutes=2),
        )

        logging.info(
            f"Setting {self.thermostat_config.entity_id} to {await self.target_temp}."
        )

        self.last_target_temp = await self.target_temp

    async def on_window_changed(self, event: Event, old_state: State, new_state: State):
        await self.apply_state()

    async def on_second_changed(self, second: int):
        await self.apply_target_temp()
