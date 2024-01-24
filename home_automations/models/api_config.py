from dataclasses import dataclass

from home_automations.const import DEFAULT_HOST, DEFAULT_PORT


@dataclass
class ApiConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
