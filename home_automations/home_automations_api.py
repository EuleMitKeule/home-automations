from datetime import datetime

from fastapi import FastAPI


class HomeAutomationsApi:
    _last_state_changed: datetime
    _last_post: datetime

    def __init__(self, fastapi: FastAPI) -> None:
        self._last_state_changed = datetime.now()
        self._last_post = datetime.now()

        fastapi.add_api_route("/status", self.get_status, methods=["GET"])
        fastapi.add_api_route("/status", self.post_status, methods=["POST"])

    async def get_status(self):
        return {
            "last_state_changed": self._last_state_changed.isoformat(),
            "last_post": self._last_post.isoformat(),
        }

    async def post_status(self):
        self._last_post = datetime.now()
        return {
            "last_state_changed": self._last_state_changed.isoformat(),
            "last_post": self._last_post.isoformat(),
        }
