import asyncio
import datetime
import logging
from typing import Any, Callable

import aiohttp
from hass_client import HomeAssistantClient as HassClient
from hass_client.exceptions import (
    AuthenticationFailed,
    CannotConnect,
    ConnectionFailed,
    NotConnected,
    NotFoundError,
)
from hass_client.models import State

from home_automations.models.config import Config
from home_automations.models.exceptions import NotFoundAgainError, ServiceTimeoutError


class HomeAssistantClient:
    config: Config
    session: aiohttp.ClientSession
    client: HassClient
    unknown_entities: set[str] = set()
    called_services: dict[int, datetime.datetime]
    on_connection_callbacks: list[Callable]

    def __init__(self, config: Config):
        """Initialize the Client class."""

        self.config = config
        self.called_services = {}
        self.on_connection_callbacks = []

    def register_on_connection(self, callback: Callable):
        """Register a callback to run when connected."""

        self.on_connection_callbacks.append(callback)

    async def connect(self):
        """Enter the Client class."""

        self.client = HassClient(
            self.config.homeassistant.url,
            self.config.homeassistant.token,
        )

        while not self.client.connected:
            try:
                await self.client.connect()
                logging.info("Connected to Home Assistant")
            except (
                NotConnected,
                CannotConnect,
                ConnectionFailed,
            ):
                logging.error("Not connected to Home Assistant, retrying in 5 seconds")
                await asyncio.sleep(5)
            except AuthenticationFailed:
                logging.error("Authentication failed")
                break

        await self.on_connected()

    async def on_connected(self):
        """Run when connected to Home Assistant."""

        for callback in self.on_connection_callbacks:
            await callback()

    async def subscribe_events(self, on_event_callback: Callable) -> Callable:
        """Subscribe to events."""

        return await self.client.subscribe_events(on_event_callback)

    async def get_state(self, entity_id: str) -> State:
        """Return the state of an entity."""

        try:
            state = await self.client.get_state(entity_id)
        except NotFoundError:
            if entity_id not in self.unknown_entities:
                self.unknown_entities.add(entity_id)
                raise
            raise NotFoundAgainError(entity_id)

        return state

    async def call_service(
        self,
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
                raise ServiceTimeoutError(
                    f"Service {domain}.{service} was called too recently"
                )

            del self.called_services[arg_hash]

        await self.client.call_service(domain, service, service_data, target)

        if timeout is not None:
            self.called_services[arg_hash] = datetime.datetime.now() + timeout
