import asyncio
import datetime
import logging

from hass_client.models import Event, State

from home_automations.const import ThermostatState
from home_automations.helper.client import Client
from home_automations.helper.clock import Clock
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
    async def should_set_state(self) -> bool:
        """Return whether the thermostat should be turned on."""

        if await self.is_switch_off:
            return False

        return True

    @property
    async def has_scheduled_temp(self) -> bool:
        """Return whether the thermostat has a scheduled temperature."""

        temp_difference = await self.temp_difference

        if temp_difference is None:
            return False

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

        current_temp = await self.current_temp
        scheduled_temp = await self.scheduled_temp

        if current_temp is None or scheduled_temp is None:
            return None

        return abs(scheduled_temp - current_temp)

    @property
    async def scheduled_temp(self) -> float | None:
        """Return the scheduled temperature for the current time."""

        return Clock.resolve_schedule(self.climate_config.schedule)

    @property
    async def target_temp(self) -> float | None:
        """Return the target temperature for the current time."""

        if await self.scheduled_temp is None or await self.current_temp is None:
            return None

        if await self.has_scheduled_temp:
            return await self.scheduled_temp

        if await self.scheduled_temp > await self.current_temp:
            return self.climate_config.max_target_temp

        return self.climate_config.min_target_temp

    @property
    async def current_state(self) -> ThermostatState:
        """Return the current state."""

        state = await self.client.get_state(self.thermostat_config.climate_entity)

        return state.state

    @property
    async def current_temp_sensor(self) -> float | None:
        state = await self.client.get_state(self.thermostat_config.temperature_entity)

        try:
            return float(state.state)
        except ValueError:
            return None

    @property
    async def current_temp_climate(self) -> float | None:
        state = await self.client.get_state(self.thermostat_config.climate_entity)

        if "temperature" not in state.attributes:
            return None

        return float(state.attributes["temperature"])

    @property
    async def current_temp(self) -> float | None:
        """Return the current temperature."""

        if self.thermostat_config.temperature_entity is not None:
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
            f"Turning {'off' if await self.target_state == ThermostatState.OFF else 'on'} {self.thermostat_config.climate_entity}."
        )

        await self.client.call_service(
            "climate",
            service,
            target={"entity_id": self.thermostat_config.climate_entity},
        )

        if await self.target_state == ThermostatState.OFF:
            return

        await self.apply_target_temp()

    async def apply_target_temp(self):
        """Apply the target temperature."""

        if not await self.should_set_temp:
            return

        if await self.target_temp is None:
            logging.warning(
                f"Could not determine target temperature for thermostat {self.thermostat_config.climate_entity}"
            )
            return

        await asyncio.sleep(0)

        await self.client.call_service(
            "climate",
            "set_temperature",
            service_data={"temperature": await self.target_temp},
            target={"entity_id": self.thermostat_config.climate_entity},
            timeout=datetime.timedelta(minutes=2),
        )

        logging.info(
            f"Setting {self.thermostat_config.climate_entity} to {await self.target_temp}."
        )

        self.last_target_temp = await self.target_temp

    async def on_window_changed(self, event: Event, old_state: State, new_state: State):
        await self.apply_state()

    async def on_second_changed(self, second: int):
        await self.apply_target_temp()

    async def on_climate_changed(
        self, event: Event, old_state: State, new_state: State
    ):
        if (
            "temperature" not in old_state.attributes
            or "temperature" not in new_state.attributes
        ):
            return

        old_target_temp = old_state.attributes["current_temperature"]
        new_target_temp = new_state.attributes["current_temperature"]

        user_id = new_state.context["user_id"]

        if (
            old_target_temp != new_target_temp
            and user_id != self.config.homeassistant.home_automations_user_id
            and len(self.thermostat_config.switch_entities) > 0
        ):
            logging.info(
                f"Assigning new target temperature {new_target_temp} to {self.thermostat_config.climate_entity}"
            )

            Clock.set_schedule(self.climate_config.schedule, new_target_temp)
            self.config.save()
