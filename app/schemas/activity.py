from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityBase(BaseModel):
    type: str
    payload: dict | None = None


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: int
    deal_id: int
    author_id: int | None
    created_at: datetime
    author_name: str | None

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
