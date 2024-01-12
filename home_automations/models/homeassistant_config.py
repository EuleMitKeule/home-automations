from dataclasses import dataclass


@dataclass
class HomeAssistantConfig:
    """Configuration for Home Assistant."""

    url: str
    token: str
    home_automations_user_id: str
