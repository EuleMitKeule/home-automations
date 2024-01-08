from abc import ABC


class ClockEvents(ABC):
    async def on_day_changed(self, day: int):
        pass

    async def on_hour_changed(self, hour: int):
        pass

    async def on_minute_changed(self, minute: int):
        pass

    async def on_second_changed(self, second: int):
        pass
