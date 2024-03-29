from dataclasses import dataclass, field


@dataclass
class DimmerConfig:
    name: str
    device_ieee: str
    light_entities: list[str] = field(default_factory=list)
