from dataclasses import dataclass


@dataclass
class NotificationConfig:
    notification_service: str
    switch_entity: str
