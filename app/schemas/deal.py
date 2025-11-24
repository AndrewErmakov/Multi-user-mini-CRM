from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DealBase(BaseModel):
    title: str
    contact_id: int
    amount: Decimal | None = None
    currency: str = "USD"
    status: str = "new"
    stage: str = "qualification"
    description: str | None = None


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    title: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: str | None = None
    stage: str | None = None
    description: str | None = None


class DealResponse(DealBase):
    id: int
    organization_id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime | None
    contact_name: str
    owner_name: str

    model_config = ConfigDict(from_attributes=True)


class DealListResponse(BaseModel):
    items: list[DealResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
