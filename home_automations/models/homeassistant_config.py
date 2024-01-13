from dataclasses import dataclass, field


@dataclass
class HomeAssistantConfig:
    """Configuration for Home Assistant."""

    url: str
    token: str
    home_automations_user_id: str = field(default="")
