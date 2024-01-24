from datetime import datetime

from pydantic import BaseModel


class Status(BaseModel):
    last_state_changed: datetime
