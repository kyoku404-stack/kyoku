from backend.app.models.task import Task
from backend.app.repositories.base import BaseRepository
from pydantic import BaseModel

class TaskRepository(BaseRepository[Task, BaseModel, BaseModel]):
    def __init__(self) -> None:
        super().__init__(Task)
