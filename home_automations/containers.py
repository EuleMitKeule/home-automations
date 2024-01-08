import os
from pathlib import Path

from dependency_injector import containers, providers

from home_automations.const import (
    DEFAULT_CONFIG_FILE_PATH,
    ENV_CONFIG_FILE_PATH,
)
from home_automations.home_automations import HomeAutomations
from home_automations.models.config import Config


class Container(containers.DeclarativeContainer):
    config_file_path_str = providers.Singleton(
        os.getenv, ENV_CONFIG_FILE_PATH, default=DEFAULT_CONFIG_FILE_PATH
    )
    config_file_path = providers.Callable(
        lambda config_file_path_str: Path(config_file_path_str)
    )
    config = providers.Singleton(Config.load, config_file_path(config_file_path_str))
    home_automations = providers.Singleton(
        HomeAutomations,
        config=config.provided,
    )
