from dataclasses import dataclass

from home_automations.models.notification_config import NotificationConfig


@dataclass
class SensorNotifyConfig:
    sensor_entity: str
    notify_on_state: str
    notification_message: str
    notification_title: str
    notification_configs: list[NotificationConfig]
