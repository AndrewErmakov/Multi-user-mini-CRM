from decimal import Decimal

from pydantic import BaseModel


class DealSummaryResponse(BaseModel):
    status_counts: dict[str, int]
    amount_by_status: dict[str, Decimal]
    average_won_amount: float
    new_deals_last_n_days: int
    days_period: int


class FunnelStage(BaseModel):
    stage: str
    total_count: int
    status_counts: dict[str, int]
    conversion_rate: float


class DealFunnelResponse(BaseModel):
    stages: list[FunnelStage]
    total_conversion: float
