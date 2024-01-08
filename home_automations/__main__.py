import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from home_automations.const import DEFAULT_CONFIG_FILE_PATH, ENV_CONFIG_FILE_PATH
from home_automations.home_automations import HomeAutomations
from home_automations.models.config import Config


async def main():
    load_dotenv()

    config_file_path: Path = Path(
        os.getenv(ENV_CONFIG_FILE_PATH, default=DEFAULT_CONFIG_FILE_PATH)
    )

    config = Config.load(config_file_path)

    if config is None:
        asyncio.get_event_loop().stop()
        return

    logging.info("Starting Home Automations")
    logging.info(f"Config file path: {config_file_path}")
    logging.info(f"Log file path: {config.logging.path}")

    home_automations = HomeAutomations(config)
    await home_automations.run()


def start():
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    start()
