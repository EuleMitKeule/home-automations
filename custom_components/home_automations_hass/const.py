from enum import StrEnum

DOMAIN = "home_automations_hass"

CONF_WASHING_MACHINE_SHELLY_ENTITY_ID = "washing_machine_shelly_entity_id"
CONF_WASHING_MACHINE_MAC = "washing_machine_mac"
CONF_WASHING_MACHINE_MANUFACTURER = "washing_machine_manufacturer"
CONF_WASHING_MACHINE_MODEL = "washing_machine_model"


class WashingMachineState(StrEnum):
    """Washing machine states."""

    OFF = "off"
    RUNNING = "running"
    FINISHED = "finished"
