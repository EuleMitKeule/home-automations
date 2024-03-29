from hass_client.models import Event, State

from home_automations.models.config import Config
from home_automations.models.sensor_notify_config import SensorNotifyConfig
from home_automations.modules.base_module import BaseModule
from home_automations.tools import Tools


class SensorNotifyModule(BaseModule):
    def __init__(
        self,
        config: Config,
        tools: Tools,
        sensor_notify_config: SensorNotifyConfig,
    ):
        super().__init__(config, tools)

        self.sensor_notify_config = sensor_notify_config

        self.register_state_changed(
            self.on_sensor_state_changed, sensor_notify_config.sensor_entity
        )

    async def on_sensor_state_changed(
        self, event: Event, old_state: State, new_state: State
    ) -> None:
        if old_state.state == new_state.state:
            return

        if new_state.state != self.sensor_notify_config.notify_on_state:
            return

        for notification_config in self.sensor_notify_config.notification_configs:
            state = await self.tools.client.get_state(notification_config.switch_entity)

            if state.state != "on":
                continue

            await self.tools.client.call_service(
                domain="notify",
                service=notification_config.notification_service,
                service_data={
                    "message": self.sensor_notify_config.notification_message,
                    "title": self.sensor_notify_config.notification_title,
                },
            )

            await self.tools.client.call_service(
                domain="input_boolean",
                service="turn_off",
                target={
                    "entity_id": notification_config.switch_entity,
                },
            )
