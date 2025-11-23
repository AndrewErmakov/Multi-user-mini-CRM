from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ContactBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    organization_id: int
    owner_id: int
    created_at: datetime
    owner_name: str

    model_config = ConfigDict(from_attributes=True)


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
