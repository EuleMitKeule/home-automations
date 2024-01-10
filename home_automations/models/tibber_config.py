from dataclasses import dataclass, field

import marshmallow

from home_automations.const import TibberLevel


@dataclass
class TibberConfig:
    token: str
    home_id: str
    level_to_color: dict[TibberLevel, str] = field(
        metadata={
            "marshmallow_field": marshmallow.fields.Dict(
                keys=marshmallow.fields.Enum(TibberLevel, by_value=True),
                values=marshmallow.fields.String(),
            )
        }
    )
    light_entities: list[str] = field(default_factory=list)