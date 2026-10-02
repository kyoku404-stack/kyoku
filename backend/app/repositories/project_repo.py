from backend.app.models.project import Project
from backend.app.repositories.base import BaseRepository
from pydantic import BaseModel


class ProjectRepository(BaseRepository[Project, BaseModel, BaseModel]):
    def __init__(self) -> None:
        super().__init__(Project)
