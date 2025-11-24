from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(  # type: ignore[var-annotated]
        Enum(
            "comment",
            "status_changed",
            "stage_changed",
            "task_created",
            "system",
            name="activity_types",
        ),
        nullable=False,
    )
    payload = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    deal = relationship("Deal", back_populates="activities")
    author = relationship("User")
