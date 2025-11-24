from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    deal_id: int


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_date: datetime | None = None
    is_done: bool | None = None


class TaskResponse(TaskBase):
    id: int
    deal_id: int
    is_done: bool
    created_at: datetime
    deal_title: str

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
