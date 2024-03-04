"""Motion light module."""

import asyncio
import logging
from datetime import datetime, timedelta

from hass_client.models import Event, State

from home_automations.models.config import Config
from home_automations.models.motion_light_config import MotionLightConfig
from home_automations.modules.base_module import BaseModule
from home_automations.tools import Tools

_LOGGER = logging.getLogger(__name__)


class MotionLightModule(BaseModule):
    def __init__(
        self,
        config: Config,
        tools: Tools,
        motion_light_config: MotionLightConfig,
    ):
        super().__init__(config, tools)

        self.motion_light_config: MotionLightConfig = motion_light_config
        self.current_task: asyncio.Task | None = None

        self.last_motion: datetime = self.tools.clock.current_datetime()
        self.last_changed: datetime = self.tools.clock.current_datetime() + timedelta(
            days=-1
        )
        self.manual_off_time: datetime = (
            self.tools.clock.current_datetime() + timedelta(days=-1)
        )

        self.is_manual_off: bool = False

        self.ignore_next_motion: bool = False
        self.ignore_motion: bool = False

        for motion_entity in self.motion_light_config.motion_entities:
            self.register_state_changed(self.on_motion_changed, motion_entity)

        for light_entity in self.motion_light_config.light_on_entities:
            self.register_state_changed(self.on_light_changed, light_entity)

        for dimmer_ieee in self.motion_light_config.dimmer_ieees:
            self.register_zha_event(self.on_dimmer_event, dimmer_ieee)

    @property
    async def current_scene(self) -> str:
        return await self.tools.day_state_resolver.resolve(self.motion_light_config)

    @property
    async def is_motion_activated(self) -> bool:
        time_difference = self.last_changed - self.last_motion

        return time_difference.total_seconds() < 0

    @property
    async def is_any_motion_on(self) -> bool:
        for motion_on_entity in self.motion_light_config.motion_entities:
            state = await self.tools.client.get_state(motion_on_entity)

            if state.state == "on":
                return True

            if state.state != "off":
                _LOGGER.warning(
                    f"[{self.motion_light_config.name}] Unknown state {state.state} for motion on entity {motion_on_entity}"
                )

        return False

    @property
    async def is_any_motion_off(self) -> bool:
        for motion_off_entity in self.motion_light_config.motion_entities:
            state = await self.tools.client.get_state(motion_off_entity)

            if state.state == "off":
                return True

            if state.state != "on":
                _LOGGER.warning(
                    f"[{self.motion_light_config.name}] Unknown state {state.state} for motion off entity {motion_off_entity}"
                )

        return False

    @property
    async def is_switch_on(self) -> bool:
        for switch_entity in self.motion_light_config.switch_entities:
            state = await self.tools.client.get_state(switch_entity)

            if state.state == "off":
                return False

            if state.state != "on":
                _LOGGER.warning(
                    f"Unknown state {state.state} for switch entity {switch_entity}"
                )

        return True

    @property
    async def all_lights_off(self) -> bool:
        for light_entity in self.motion_light_config.light_on_entities:
            state = await self.tools.client.get_state(light_entity)

            if state.state != "off":
                return False

        return True

    async def on_off(self):
        pass

    async def on_on(self):
        pass

    async def on_press(self):
        pass

    async def on_hold(self):
        pass

    async def on_release(self):
        pass

    async def on_dimmer_event(self, event: Event, device_ieee: str):
        if "command" not in event.data:
            return

        command = event.data["command"]

        if (
            command is not None
            and command != ""
            and command != "attribute_updated"
            and command != "checkin"
        ):
            await self.on_user_changed()

        match command:
            case "off":
                await self.on_user_off()
            case "on":
                await self.on_user_on()
            case "press":
                await self.on_user_on()
            case "hold":
                await self.on_user_on()
            case "release":
                await self.on_user_on()

    async def on_motion_on(self):
        _LOGGER.debug(f"[{self.motion_light_config.name}] Motion on")

        if self.current_task is not None and not self.current_task.done():
            _LOGGER.debug(f"[{self.motion_light_config.name}] Cancelling off task")
            self.current_task.cancel()

        manual_off_time_difference = (
            self.tools.clock.current_datetime() - self.manual_off_time
        )

        if (
            manual_off_time_difference.total_seconds()
            < self.motion_light_config.off_override_time
        ):
            _LOGGER.debug(
                f"[{self.motion_light_config.name}] Manual off override, not turning on"
            )
            self.is_manual_off = True
            return

        # if self.ignore_next_motion:
        #     self.ignore_next_motion = False
        #     return

        # if self.ignore_motion:
        #     return

        if not await self.all_lights_off:
            _LOGGER.debug(f"[{self.motion_light_config.name}] Lights already on")
            return

        scene = await self.current_scene

        _LOGGER.debug(f"[{self.motion_light_config.name}] Turning on scene {scene}")

        async def turn_on():
            await asyncio.sleep(self.motion_light_config.on_delay)
            await self.tools.client.call_service(
                "scene",
                "turn_on",
                target={
                    "entity_id": scene,
                },
            )

        self.current_task = self.tools.loop.create_task(turn_on())
        self.last_motion = self.tools.clock.current_datetime()

    async def on_motion_off(self):
        _LOGGER.debug(f"[{self.motion_light_config.name}] Motion off")

        if self.current_task is not None and not self.current_task.done():
            _LOGGER.debug(f"[{self.motion_light_config.name}] Cancelling on task")
            self.current_task.cancel()

        if self.is_manual_off:
            self.is_manual_off = False
            self.manual_off_time = self.tools.clock.current_datetime()

        if await self.is_any_motion_on:
            return

        time_difference = self.last_changed - self.last_motion

        if time_difference.total_seconds() > 0:
            _LOGGER.debug(
                f"[{self.motion_light_config.name}] Light changed by user, not turning off"
            )
            return

        async def turn_off():
            await asyncio.sleep(self.motion_light_config.off_delay)
            for light_entity in self.motion_light_config.light_on_entities:
                await self.tools.client.call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": light_entity},
                )

        self.current_task = self.tools.loop.create_task(turn_off())

    async def on_user_changed(self):
        self.last_changed = self.tools.clock.current_datetime()

    async def on_user_on(self):
        pass
        # self.ignore_motion = False
        # self.last_motion = self.last_changed + timedelta(seconds=1)
        # self.ignore_next_motion = False

    async def on_user_off(self):
        self.is_manual_off = True

        if await self.is_any_motion_off:
            self.is_manual_off = False
            self.manual_off_time = self.tools.clock.current_datetime()

        # self.ignore_motion = True

        # if await self.is_motion_activated:
        #     self.ignore_motion = True
        #     # self.ignore_next_motion = True

    async def on_motion_changed(self, event: Event, old_state: State, new_state: State):
        if not await self.is_switch_on:
            return

        if old_state.state == new_state.state:
            return

        _LOGGER.debug(
            "[%s] Motion changed from %s to %s",
            self.motion_light_config.name,
            old_state.state,
            new_state.state,
        )

        if new_state.state == "on":
            await self.on_motion_on()
        else:
            await self.on_motion_off()

    async def on_light_changed(self, event: Event, old_state: State, new_state: State):
        if (
            old_state.state == new_state.state
            and old_state.attributes.get("brightness")
            == new_state.attributes.get("brightness")
            and old_state.attributes.get("color_temp")
            == new_state.attributes.get("color_temp")
            and old_state.attributes.get("rgb_color")
            == new_state.attributes.get("rgb_color")
        ):
            return

        user_id = new_state.context.get("user_id")

        if (
            user_id == self.config.homeassistant.home_automations_user_id
            or user_id is None
        ):
            return

        _LOGGER.debug(
            f"[{self.motion_light_config.name}] Light {new_state.entity_id} changed by user from {old_state.state} to {new_state.state}"
        )

        if old_state.state != new_state.state and new_state.state == "off":
            await self.on_user_off()

        await self.on_user_changed()

        if old_state.state != new_state.state and new_state.state == "on":
            await self.on_user_on()
