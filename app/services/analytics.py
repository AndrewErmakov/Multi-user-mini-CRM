import json
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.models import Deal


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_deal_summary(self, organization_id: int, days: int = 30) -> dict:
        """
        Получает сводку по сделкам для организации с кэшированием
        """
        # Проверяем кэш с учетом параметра days
        cache_key = f"deal_summary:{organization_id}:{days}"
        redis_client = await cache_manager.get_redis()
        cached_result = await redis_client.get(cache_key)

        if cached_result:
            return json.loads(cached_result)

        # Получаем количество сделок и сумму по статусам
        result = await self.db.execute(
            select(
                Deal.status,
                func.count(Deal.id).label("count"),
                func.coalesce(func.sum(Deal.amount), Decimal("0")).label("total_amount"),
            )
            .where(Deal.organization_id == organization_id)
            .group_by(Deal.status)
        )
        status_data = result.all()

        status_counts = {}
        amount_by_status = {}

        for status, count, total_amount in status_data:
            status_counts[status] = count
            amount_by_status[status] = total_amount

        # Получаем среднюю сумму выигранных сделок
        result = await self.db.execute(
            select(func.avg(Deal.amount)).where(
                Deal.organization_id == organization_id, Deal.status == "won", Deal.amount > 0
            )
        )
        avg_won_amount = result.scalar() or Decimal("0")

        # Получаем количество новых сделок за указанное количество дней
        days_ago = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(func.count(Deal.id)).where(
                Deal.organization_id == organization_id,
                Deal.created_at >= days_ago,
                Deal.status == "new",
            )
        )
        new_deals_last_n_days = result.scalar() or 0

        result_data = {
            "status_counts": status_counts,
            "amount_by_status": amount_by_status,
            "average_won_amount": float(avg_won_amount) if avg_won_amount else 0.0,
            "new_deals_last_n_days": new_deals_last_n_days,
            "days_period": days,
        }

        await redis_client.setex(cache_key, 300, json.dumps(result_data, default=str))

        return result_data

    async def get_deal_funnel(self, organization_id: int) -> dict:
        """
        Получает воронку продаж для организации с кэшированием
        """
        # Проверяем кэш
        cache_key = f"deal_funnel:{organization_id}"
        redis_client = await cache_manager.get_redis()
        cached_result = await redis_client.get(cache_key)

        if cached_result:
            return json.loads(cached_result)

        # Получаем количество сделок по стадиям и статусам
        result = await self.db.execute(
            select(Deal.stage, Deal.status, func.count(Deal.id).label("count"))
            .where(Deal.organization_id == organization_id)
            .group_by(Deal.stage, Deal.status)
        )
        stage_data = result.all()

        # Организуем данные по стадиям
        stages_order = ["qualification", "proposal", "negotiation", "closed"]
        stage_counts = {stage: {"total": 0, "status_counts": {}} for stage in stages_order}

        for stage, status, count in stage_data:
            if stage in stage_counts:
                stage_counts[stage]["total"] += count
                stage_counts[stage]["status_counts"][status] = (
                    stage_counts[stage]["status_counts"].get(status, 0) + count
                )

        # Рассчитываем конверсию между стадиями
        funnel_stages = []

        for i, stage in enumerate(stages_order):
            current_stage = stage_counts[stage]
            current_count = current_stage["total"]

            # Рассчитываем конверсию из предыдущей стадии
            if i == 0:
                conversion_rate = 100.0  # Первая стадия всегда 100%
            else:
                previous_stage = stages_order[i - 1]
                previous_count = stage_counts[previous_stage]["total"]
                conversion_rate = (
                    (current_count / previous_count * 100) if previous_count > 0 else 0.0
                )

            funnel_stages.append(
                {
                    "stage": stage,
                    "total_count": current_count,
                    "status_counts": current_stage["status_counts"],
                    "conversion_rate": round(conversion_rate, 2),
                }
            )

        # Рассчитываем общую конверсию (от первой до последней стадии)
        first_stage_count = stage_counts[stages_order[0]]["total"]
        last_stage_count = stage_counts[stages_order[-1]]["total"]
        total_conversion = (
            (last_stage_count / first_stage_count * 100) if first_stage_count > 0 else 0.0
        )

        result_data = {"stages": funnel_stages, "total_conversion": round(total_conversion, 2)}

        await redis_client.setex(cache_key, 300, json.dumps(result_data, default=str))

        return result_data

    async def invalidate_analytics_cache(self, organization_id: int):
        """
        Инвалидирует кэш аналитики для организации
        """
        redis_client = await cache_manager.get_redis()

        pattern = f"deal_summary:{organization_id}:*"
        keys = await redis_client.keys(pattern)

        if keys:
            await redis_client.delete(*keys)

        funnel_key = f"deal_funnel:{organization_id}"
        await redis_client.delete(funnel_key)
