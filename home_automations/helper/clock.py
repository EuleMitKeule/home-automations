from abc import ABC
from datetime import datetime, time
from typing import Any

import pytz
from pytz.tzinfo import BaseTzInfo

from home_automations.const import DEFAULT_TZ
from home_automations.helper.clock_events import ClockEvents
from home_automations.models.config import Config


class Clock(ABC):
    tz: BaseTzInfo = pytz.timezone(DEFAULT_TZ)
    last_day: int = -1
    last_hour: int = -1
    last_minute: int = -1
    last_second: int = -1

    clock_events: list[ClockEvents] = []

    @classmethod
    def register_module(cls, module: ClockEvents):
        cls.clock_events.append(module)

    @classmethod
    async def run(cls):
        if cls.current_day != cls.last_day:
            cls.last_day = cls.current_day
            for module in cls.clock_events:
                await module.on_day_changed(cls.current_day)

        if cls.current_hour != cls.last_hour:
            cls.last_hour = cls.current_hour
            for module in cls.clock_events:
                await module.on_hour_changed(cls.current_hour)

        if cls.current_minute != cls.last_minute:
            cls.last_minute = cls.current_minute
            for module in cls.clock_events:
                await module.on_minute_changed(cls.current_minute)

        if cls.current_second != cls.last_second:
            cls.last_second = cls.current_second
            for module in cls.clock_events:
                await module.on_second_changed(cls.current_second)

    @classmethod
    async def init(cls, config: Config):
        Clock.tz = pytz.timezone(config.timezone)

    @classmethod
    @property
    def current_time(cls) -> time:
        return datetime.now(Clock.tz).time()

    @classmethod
    @property
    def current_day(cls) -> int:
        return datetime.now(Clock.tz).day

    @classmethod
    @property
    def current_hour(cls) -> int:
        return datetime.now(Clock.tz).hour

    @classmethod
    @property
    def current_minute(cls) -> int:
        return datetime.now(Clock.tz).minute

    @classmethod
    @property
    def current_second(cls) -> int:
        return datetime.now(Clock.tz).second

    @classmethod
    def parse_time(cls, time_string: str) -> time:
        if ":" in time_string:
            format_string = "%H:%M:%S" if len(time_string.split(":")) == 3 else "%H:%M"
        else:
            format_string = "%H"

        parsed_time = datetime.strptime(time_string, format_string).time()

        return parsed_time

    @classmethod
    def resolve_schedule(cls, schedule: dict[str, Any]) -> str:
        """Return the maximum time reached in the schedule."""

        schedule_key = cls._get_schedule_key(schedule)

        return schedule[schedule_key]

    @classmethod
    def set_schedule(cls, schedule: dict[str, Any], value) -> dict[str, Any]:
        """Set the schedule."""

        schedule_key = cls._get_schedule_key(schedule)

        schedule[schedule_key] = value

        return schedule

    @classmethod
    def _get_schedule_key(cls, schedule: dict[str, Any]) -> str:
        max_time_reached = cls.parse_time("00:00:00")
        max_time = cls.parse_time("00:00:00")
        max_key_reached: str | None = None
        max_key: str | None = None

        if len(schedule) == 1:
            return list(schedule.keys())[0]

        for time_key in schedule.keys():
            time = cls.parse_time(time_key)

            if time > max_time_reached and time <= cls.current_time:
                max_time_reached = time
                max_key_reached = time_key

            if time > max_time:
                max_time = time
                max_key = time_key

        if max_key_reached is None:
            return max_key

        return max_key_reached
