from dataclasses import dataclass


@dataclass
class HomeAssistantConfig:
    """Configuration for Home Assistant."""

    url: str
    token: str
