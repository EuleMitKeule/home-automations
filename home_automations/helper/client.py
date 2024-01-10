import asyncio
import logging
from datetime import time

from hass_client import HomeAssistantClient
from hass_client.exceptions import (
    AuthenticationFailed,
    CannotConnect,
    ConnectionFailed,
    NotConnected,
    NotFoundError,
)

from home_automations.models.config import Config
from home_automations.models.exceptions import NotFoundAgainError


class Client:
    hass_client: HomeAssistantClient
    config: Config
    unknown_entities: set[str] = set()

    def __init__(self, config: Config):
        """Initialize the Client class."""

        self.config = config
        self.hass_client = HomeAssistantClient(
            config.homeassistant.url, config.homeassistant.token
        )

    async def connect(self):
        """Connect to Home Assistant."""

        while not self.hass_client.connected:
            try:
                await self.hass_client.connect()
            except (NotConnected, CannotConnect, ConnectionFailed):
                logging.error("Not connected to Home Assistant, retrying in 5 seconds")
                await asyncio.sleep(5)
            except AuthenticationFailed:
                logging.error("Authentication failed")
                break

    async def run(self, on_event_callback: callable):
        """Run the Client class."""

        await self.connect()
        await self.hass_client.subscribe_events(on_event_callback)

    async def get_state(self, entity_id: str) -> str:
        """Return the state of an entity."""

        if not self.hass_client.connected:
            await self.connect()

        try:
            state = await self.hass_client.get_state(entity_id)
        except NotFoundError:
            if entity_id not in self.unknown_entities:
                self.unknown_entities.add(entity_id)
                raise
            raise NotFoundAgainError(entity_id)

        return state

    async def call_service(self, domain: str, service: str, **kwargs):
        """Call a service."""

        if not self.hass_client.connected:
            await self.connect()

        await self.hass_client.call_service(domain, service, **kwargs)
