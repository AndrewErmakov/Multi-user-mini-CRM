import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.error_handlers import map_domain_exception_to_http
from app.api.v1.endpoints import (
    activities_router,
    analytics_router,
    auth_router,
    contacts_router,
    deals_router,
    organizations_router,
    tasks_router,
)
from app.core.config import settings
from app.core.exceptions import DomainException
from app.database.base import Base
from app.database.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(
    organizations_router, prefix=f"{settings.API_V1_STR}/organizations", tags=["organizations"]
)
app.include_router(contacts_router, prefix=f"{settings.API_V1_STR}/contacts", tags=["contacts"])
app.include_router(deals_router, prefix=f"{settings.API_V1_STR}/deals", tags=["deals"])
app.include_router(tasks_router, prefix=f"{settings.API_V1_STR}/tasks", tags=["tasks"])
app.include_router(
    activities_router, prefix=f"{settings.API_V1_STR}/activities", tags=["activities"]
)
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    http_exception = map_domain_exception_to_http(exc)
    return JSONResponse(
        status_code=http_exception.status_code,
        content={"detail": http_exception.detail},
    )


@app.on_event("startup")
async def startup():
    if not settings.TESTING:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    else:
        logger.info("Running in TESTING mode - skipping database table creation")


@app.get("/")
async def root():
    return {"message": "Mini-CRM API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
