from enum import StrEnum

DOMAIN = "home_automations_hass"


class WashingMachineState(StrEnum):
    """Washing machine states."""

    OFF = "off"
    RUNNING = "running"
    FINISHED = "finished"
