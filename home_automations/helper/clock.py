import asyncio
from datetime import date, datetime, time, timedelta
from typing import Any, Callable

import pytz
from pytz.tzinfo import BaseTzInfo

from home_automations.helper.clock_events import ClockEvents
from home_automations.models.config import Config


class Clock:
    def __init__(self, config: Config):
        """Initialize the Clock class."""

        self.config: Config = config
        self.tz: BaseTzInfo = pytz.timezone(config.timezone)
        self.last_day: int = -1
        self.last_hour: int = -1
        self.last_minute: int = -1
        self.last_second: int = -1
        self.clock_events: list[ClockEvents] = []
        self.scheduled_tasks: list[tuple[Callable, timedelta, datetime]] = []

    def register_module(self, module: ClockEvents):
        self.clock_events.append(module)

    def register_task(self, task: Callable, interval: timedelta):
        if interval.total_seconds() < 1:
            raise ValueError("Interval must be at least 1 second")
        self.scheduled_tasks.append((task, interval, datetime.now()))

    async def run(self):
        loop = asyncio.get_running_loop()
        if self.current_day() != self.last_day:
            self.last_day = self.current_day()
            for module in self.clock_events:
                loop.create_task(module.on_day_changed(self.current_day()))

        if self.current_hour() != self.last_hour:
            self.last_hour = self.current_hour()
            for module in self.clock_events:
                loop.create_task(module.on_hour_changed(self.current_hour()))

        if self.current_minute() != self.last_minute:
            self.last_minute = self.current_minute()
            for module in self.clock_events:
                loop.create_task(module.on_minute_changed(self.current_minute()))

        if self.current_second() != self.last_second:
            self.last_second = self.current_second()
            for module in self.clock_events:
                loop.create_task(module.on_second_changed(self.current_second()))
                loop.create_task(self.run_tasks())

    async def run_tasks(self):
        loop = asyncio.get_running_loop()

        invoked_tasks: list[tuple[Callable, timedelta, datetime]] = []

        for i, (task, interval, last_run) in enumerate(self.scheduled_tasks):
            if datetime.now() - last_run >= interval:
                loop.create_task(task())

                entry = self.scheduled_tasks.pop(i)

                invoked_tasks.append(entry)

        for task, interval, last_run in invoked_tasks:
            self.scheduled_tasks.append((task, interval, datetime.now()))

    def current_datetime(self) -> datetime:
        return datetime.now(self.tz)

    def current_date(self) -> date:
        return datetime.now(self.tz).date()

    def current_time(self) -> time:
        return datetime.now(self.tz).time()

    def current_day(self) -> int:
        return datetime.now(self.tz).day

    def current_hour(self) -> int:
        return datetime.now(self.tz).hour

    def current_minute(self) -> int:
        return datetime.now(self.tz).minute

    def current_second(self) -> int:
        return datetime.now(self.tz).second

    def parse_time(self, time_string: str) -> time:
        if ":" in time_string:
            format_string = "%H:%M:%S" if len(time_string.split(":")) == 3 else "%H:%M"
        else:
            format_string = "%H"

        parsed_time = datetime.strptime(time_string, format_string).time()

        return parsed_time

    def resolve_schedule(self, schedule: dict[str, Any]) -> Any:
        """Return the maximum value reached in the schedule."""

        schedule_key = self._get_schedule_key(schedule)

        return schedule[schedule_key]

    def set_schedule(self, schedule: dict[str, Any], value) -> dict[str, Any]:
        """Set the schedule."""

        schedule_key = self._get_schedule_key(schedule)

        schedule[schedule_key] = value

        return schedule

    def _get_schedule_key(self, schedule: dict[str, Any]) -> str:
        max_time_reached = self.parse_time("00:00:00")
        max_time = self.parse_time("00:00:00")
        max_key_reached: str | None = None
        max_key: str = list(schedule.keys())[0]

        if len(schedule) == 0:
            raise ValueError("Schedule is empty")

        if len(schedule) == 1:
            return max_key

        for time_key in schedule.keys():
            time = self.parse_time(time_key)

            if time > max_time_reached and time <= self.current_time():
                max_time_reached = time
                max_key_reached = time_key

            if time > max_time:
                max_time = time
                max_key = time_key

        if max_key_reached is None:
            return max_key

        return max_key_reached
