from dataclasses import dataclass, field

from home_automations.models.state_condition_config import StateConditionConfig


@dataclass
class LightReplacementConfig:
    light_entity: str
    light_replacement_entity: str
    conditions: list[StateConditionConfig] = field(default_factory=list)
