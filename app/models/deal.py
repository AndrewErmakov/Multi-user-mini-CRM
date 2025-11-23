from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")  # USD, EUR, etc.
    status = Column(Enum("new", "in_progress", "won", "lost", name="deal_statuses"), default="new")
    stage = Column(
        Enum("qualification", "proposal", "negotiation", "closed", name="deal_stages"),
        default="qualification",
    )
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    contact = relationship("Contact", back_populates="deals")
    owner = relationship("User")
    tasks = relationship("Task", back_populates="deal")
    activities = relationship("Activity", back_populates="deal")
