import asyncio
import datetime
import logging
from typing import Any

import aiohttp
from hass_client import HomeAssistantClient
from hass_client.exceptions import (
    AuthenticationFailed,
    CannotConnect,
    ConnectionFailed,
    NotConnected,
    NotFoundError,
)
from hass_client.models import State

from home_automations.models.config import Config
from home_automations.models.exceptions import NotFoundAgainError


class Client:
    config: Config
    unknown_entities: set[str] = set()
    called_services: dict[int, datetime.datetime] = {}

    def __init__(self, config: Config):
        """Initialize the Client class."""

        self.config = config

    async def with_client(self, func: callable):
        """Run a function with the hass_client."""

        async with aiohttp.ClientSession() as session:
            client = HomeAssistantClient(
                self.config.homeassistant.url,
                self.config.homeassistant.token,
                aiohttp_session=session,
            )

            while not client.connected:
                try:
                    await client.connect()
                except (NotConnected, CannotConnect, ConnectionFailed):
                    logging.error(
                        "Not connected to Home Assistant, retrying in 5 seconds"
                    )
                    await asyncio.sleep(5)
                except AuthenticationFailed:
                    logging.error("Authentication failed")
                    break

            try:
                result = await func(client)
            finally:
                await client.disconnect()

            return result

    async def subscribe_events(self, on_event_callback: callable):
        """Subscribe to events."""

        await self.with_client(
            lambda client: self._subscribe_events(client, on_event_callback)
        )

    async def _subscribe_events(
        self, client: HomeAssistantClient, on_event_callback: callable
    ):
        """Subscribe to events."""

        await client.subscribe_events(on_event_callback)

    async def get_state(self, entity_id: str) -> State:
        """Return the state of an entity."""

        return await self.with_client(lambda client: self._get_state(client, entity_id))

    async def _get_state(self, client: HomeAssistantClient, entity_id: str) -> State:
        """Return the state of an entity."""

        try:
            state = await client.get_state(entity_id)
        except NotFoundError:
            if entity_id not in self.unknown_entities:
                self.unknown_entities.add(entity_id)
                raise
            raise NotFoundAgainError(entity_id)

        return state

    async def call_service(self, domain: str, service: str, **kwargs):
        """Call a service."""

        await self.with_client(
            lambda client: self._call_service(client, domain, service, **kwargs)
        )

    async def _call_service(
        self,
        client: HomeAssistantClient,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
        timeout: datetime.timedelta | None = None,
    ):
        """Call a service."""

        arg_hash = hash(
            (
                domain,
                service,
                frozenset(service_data) if service_data is not None else None,
                frozenset(target) if target is not None else None,
            )
        )

        if arg_hash in self.called_services:
            if self.called_services[arg_hash] > datetime.datetime.now():
                return

            del self.called_services[arg_hash]

        await client.call_service(domain, service, service_data, target)

        if timeout is not None:
            self.called_services[arg_hash] = datetime.datetime.now() + timeout