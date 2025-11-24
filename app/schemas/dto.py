from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ContactCreateDTO(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    organization_id: int
    owner_id: int


class DealCreateDTO(BaseModel):
    title: str
    contact_id: int
    organization_id: int
    owner_id: int
    amount: Decimal | None = None
    currency: str = "USD"
    status: str = "new"
    stage: str = "qualification"


class TaskCreateDTO(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    deal_id: int
