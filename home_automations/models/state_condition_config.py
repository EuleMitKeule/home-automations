from dataclasses import dataclass


@dataclass
class StateConditionConfig:
    entity: str
    state: str
