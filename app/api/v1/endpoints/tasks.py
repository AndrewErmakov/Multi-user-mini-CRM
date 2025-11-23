from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_organization, get_current_user
from app.database.session import get_db
from app.schemas import TaskCreate, TaskListResponse, TaskResponse
from app.schemas.dto import TaskCreateDTO
from app.services import TaskService

router = APIRouter()


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    deal_id: int | None = Query(None),
    only_open: bool = Query(False),
    due_before: datetime | None = Query(None),
    due_after: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    task_service = TaskService(db)
    result = await task_service.get_tasks(
        organization_id=org_context["organization_id"],
        page=page,
        page_size=page_size,
        deal_id=deal_id,
        only_open=only_open,
        due_before=due_before,
        due_after=due_after,
    )
    return result


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    org_context=Depends(get_current_organization),
):
    task_service = TaskService(db)

    task_dto = TaskCreateDTO(**task_data.model_dump())

    task = await task_service.create_task(
        task_dto,
        current_user.id,
        org_context["user_role"],
        org_context["organization_id"]
    )
    return task
