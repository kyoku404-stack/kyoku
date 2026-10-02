from backend.app.models.meeting import Meeting
from backend.app.repositories.base import BaseRepository
from pydantic import BaseModel


class MeetingRepository(BaseRepository[Meeting, BaseModel, BaseModel]):
    def __init__(self) -> None:
        super().__init__(Meeting)
