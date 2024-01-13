import logging

from hass_client.models import Event, State

from home_automations.const import ThermostatState
from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
from home_automations.helper.math import Math
from home_automations.models.climate_config import ClimateConfig
from home_automations.models.config import Config
from home_automations.models.thermostat_config import ThermostatConfig
from home_automations.modules.base_module import BaseModule


class ThermostatModule(BaseModule):
    """Module for controlling a thermostat."""

    def __init__(
        self,
        config: Config,
        client: Client,
        climate_config: ClimateConfig,
        thermostat_config: ThermostatConfig,
    ):
        super().__init__(config, client)

        self.climate_config = climate_config
        self.thermostat_config = thermostat_config

        for window_entity in self.thermostat_config.window_entities:
            self.register_state_changed(self.on_window_changed, window_entity)

        self.register_state_changed(
            self.on_climate_changed, self.thermostat_config.climate_entity
        )

    @property
    async def is_window_open(self) -> bool:
        """Return whether one of the windows is open."""

        is_open: bool = False

        for window in self.thermostat_config.window_entities:
            state = await self.client.get_state(window)

            if state.state == "on":
                is_open = True

        return is_open

    @property
    async def is_switch_off(self) -> bool:
        """Return whether any of the switches are off."""

        for switch in self.thermostat_config.switch_entities:
            state = await self.client.get_state(switch)

            if state.state == "off":
                return True

        return False

    @property
    async def current_room_temp(self) -> float | None:
        state = await self.client.get_state(self.thermostat_config.temperature_entity)

        try:
            return float(state.state)
        except ValueError:
            return None

    @property
    async def target_room_temp(self) -> float:
        """Return the target room temperature."""

        return Clock.resolve_schedule(self.climate_config.schedule)

    @property
    async def room_temp_difference(self) -> float | None:
        """Return the difference between the current and target temperature."""

        current_temp = await self.current_room_temp
        target_temp = await self.target_room_temp

        if current_temp is None:
            return None

        return abs(target_temp - current_temp)

    @property
    async def current_thermostat_state(self) -> ThermostatState:
        """Return the current state."""

        state = await self.client.get_state(self.thermostat_config.climate_entity)

        return state.state

    @property
    async def target_thermostat_state(self) -> ThermostatState:
        """Return the target state for the thermostat."""

        if await self.is_window_open:
            return ThermostatState.OFF

        return ThermostatState.HEAT

    @property
    async def current_thermostat_target_temp(self) -> float | None:
        state = await self.client.get_state(self.thermostat_config.climate_entity)

        if "temperature" not in state.attributes:
            return None

        return float(state.attributes["temperature"])

    @property
    async def current_thermostat_temp(self) -> float | None:
        state = await self.client.get_state(self.thermostat_config.climate_entity)

        if "current_temperature" not in state.attributes:
            return None

        return float(state.attributes["current_temperature"])

    @property
    async def target_thermostat_temp(self) -> float | None:
        """Return the target temperature for the current time."""

        room_temp_difference = await self.room_temp_difference
        current_room_temp = await self.current_room_temp

        if room_temp_difference is None or current_room_temp is None:
            return None

        room_temp_difference = (
            min(self.climate_config.max_target_diff, room_temp_difference)
            / self.climate_config.max_target_diff
        )

        from_value = (
            self.climate_config.min_effective_thermostat_temp
            if current_room_temp > await self.target_room_temp
            else self.climate_config.max_effective_thermostat_temp
        )

        return Math.round_to_nearest_half(
            Math.lerp(from_value, await self.target_room_temp, room_temp_difference)
        )

    async def set_thermostat_state(self, state: ThermostatState):
        """Set the thermostat state."""

        if await self.is_switch_off:
            return

        if await self.current_thermostat_state == state:
            return

        if await self.current_thermostat_state == ThermostatState.UNAVAILABLE:
            return

        service = "turn_off" if state == ThermostatState.OFF else "turn_on"

        logging.info(
            f"Turning {'off' if state == ThermostatState.OFF else 'on'} {self.thermostat_config.climate_entity}."
        )

        await self.client.call_service(
            "climate",
            service,
            target={"entity_id": self.thermostat_config.climate_entity},
        )

    async def set_thermostat_temp(self, temp: float):
        """Set the thermostat temperature."""

        if await self.is_switch_off:
            return

        target_state = await self.target_thermostat_state

        if target_state == ThermostatState.OFF:
            return

        if await self.current_thermostat_state == ThermostatState.UNAVAILABLE:
            return

        if temp < self.climate_config.min_effective_thermostat_temp:
            await self.set_thermostat_state(ThermostatState.OFF)
            return

        temp = min(temp, self.climate_config.max_effective_thermostat_temp)

        if temp == await self.current_thermostat_target_temp:
            return

        logging.info(f"Setting {self.thermostat_config.climate_entity} to {temp}.")

        await self.client.call_service(
            "climate",
            "set_temperature",
            service_data={"temperature": temp},
            target={"entity_id": self.thermostat_config.climate_entity},
        )

    async def on_window_changed(self, event: Event, old_state: State, new_state: State):
        """Handle a window change event."""

        if new_state.state == old_state.state:
            return

        await self.set_thermostat_state(await self.target_thermostat_state)

    async def on_second_changed(self, second: int):
        target_thermostat_temp = await self.target_thermostat_temp

        if target_thermostat_temp is None:
            return

        await self.set_thermostat_temp(target_thermostat_temp)

    async def on_climate_changed(
        self, event: Event, old_state: State, new_state: State
    ):
        if (
            "temperature" not in old_state.attributes
            or "temperature" not in new_state.attributes
        ):
            return

        old_target_temp = old_state.attributes["temperature"]
        new_target_temp = new_state.attributes["temperature"]

        user_id = new_state.context["user_id"]

        if (
            old_target_temp != new_target_temp
            and user_id != self.config.homeassistant.home_automations_user_id
        ):
            logging.info(
                f"Assigning new target temperature {new_target_temp} to {self.thermostat_config.climate_entity}"
            )

            Clock.set_schedule(self.climate_config.schedule, new_target_temp)
            self.config.save()
