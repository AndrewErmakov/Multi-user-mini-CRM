from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DealNotFoundException, ValidationException
from app.repositories import ActivityRepository, DealRepository
from app.schemas import ActivityResponse


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_repo = ActivityRepository(db)
        self.deal_repo = DealRepository(db)

    async def create_activity(
        self, deal_id: int, activity_data: dict, organization_id: int, author_id: int
    ) -> ActivityResponse:
        deal = await self.deal_repo.get_deal_with_organization(deal_id, organization_id)
        if not deal:
            raise DealNotFoundException("Deal not found in organization")

        if activity_data.get("type") != "comment":
            raise ValidationException("Only comment activities can be created via API")

        if activity_data.get("type") == "comment":
            payload = activity_data.get("payload", {})
            if "text" not in payload or not payload["text"].strip():
                raise ValidationException("Comment activity must have text in payload")

        activity_data.update({"deal_id": deal_id, "author_id": author_id})

        activity = await self.activity_repo.create(activity_data)

        return ActivityResponse(
            id=activity.id,
            deal_id=activity.deal_id,
            author_id=activity.author_id,
            type=activity.type,
            payload=activity.payload,
            created_at=activity.created_at,
            author_name=f"User {activity.author_id}" if activity.author_id else "System",
        )

    async def get_deal_activities(
        self, deal_id: int, organization_id: int, page: int = 1, page_size: int = 100
    ) -> dict:
        deal = await self.deal_repo.get_deal_with_organization(deal_id, organization_id)
        if not deal:
            raise DealNotFoundException("Deal not found in organization")

        skip = (page - 1) * page_size
        activities = await self.activity_repo.get_deal_activities(
            deal_id, organization_id, skip, page_size
        )
        total = await self.activity_repo.count_deal_activities(deal_id, organization_id)

        activity_responses = [
            ActivityResponse(
                id=activity.id,
                deal_id=activity.deal_id,
                author_id=activity.author_id,
                type=activity.type,
                payload=activity.payload,
                created_at=activity.created_at,
                author_name=f"User {activity.author_id}" if activity.author_id else "System",
            )
            for activity in activities
        ]

        return {
            "items": activity_responses,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
