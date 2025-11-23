import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import AnalyticsService


class TestAnalyticsService:
    @pytest.mark.asyncio
    async def test_get_deal_summary_success(self, test_session: AsyncSession):
        analytics_service = AnalyticsService(test_session)

        # Создаем моки для каждого вызова execute
        mock_result1 = MagicMock()  # Для первого вызова - статусы
        mock_result1.all.return_value = [
            ("new", 5, Decimal("0")),
            ("in_progress", 3, Decimal("15000")),
            ("won", 2, Decimal("50000")),
            ("lost", 1, Decimal("0")),
        ]

        mock_result2 = MagicMock()  # Для второго вызова - среднее значение
        mock_result2.scalar.return_value = Decimal("25000")

        mock_result3 = MagicMock()  # Для третьего вызова - количество новых сделок
        mock_result3.scalar.return_value = 2

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.services.analytics.cache_manager.get_redis", return_value=mock_redis):
            with patch.object(analytics_service.db, "execute") as mock_execute:
                # Используем side_effect для последовательных возвратов
                mock_execute.side_effect = [mock_result1, mock_result2, mock_result3]

                result = await analytics_service.get_deal_summary(organization_id=1, days=30)

        assert result["status_counts"]["new"] == 5
        assert result["status_counts"]["won"] == 2
        assert result["amount_by_status"]["in_progress"] == Decimal("15000")
        assert result["average_won_amount"] == 25000.0
        assert result["new_deals_last_n_days"] == 2
        assert result["days_period"] == 30

    @pytest.mark.asyncio
    async def test_get_deal_summary_with_cache(self, test_session: AsyncSession):
        analytics_service = AnalyticsService(test_session)

        # Создаем данные для кэша с учетом того, что JSON сериализует Decimal в строку
        cached_data = {
            "status_counts": {"new": 3, "won": 1},
            "amount_by_status": {"new": "0", "won": "10000"},  # Decimal как строки
            "average_won_amount": 10000.0,
            "new_deals_last_n_days": 1,
            "days_period": 30,
        }

        # Mock Redis with cached data
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(cached_data, default=str)

        with patch("app.services.analytics.cache_manager.get_redis", return_value=mock_redis):
            result = await analytics_service.get_deal_summary(organization_id=1, days=30)

        # Проверяем что данные возвращаются из кэша (строки остаются строками)
        assert result["status_counts"] == cached_data["status_counts"]
        assert result["amount_by_status"] == cached_data["amount_by_status"]  # Строки, а не Decimal
        assert result["average_won_amount"] == cached_data["average_won_amount"]
        assert result["new_deals_last_n_days"] == cached_data["new_deals_last_n_days"]
        assert result["days_period"] == cached_data["days_period"]

        mock_redis.get.assert_called_once_with("deal_summary:1:30")

    @pytest.mark.asyncio
    async def test_get_deal_funnel_success(self, test_session: AsyncSession):
        analytics_service = AnalyticsService(test_session)

        # Mock database results
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("qualification", "new", 5),
            ("qualification", "in_progress", 2),
            ("proposal", "in_progress", 3),
            ("negotiation", "won", 2),
            ("closed", "won", 1),
        ]

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()

        with patch("app.services.analytics.cache_manager.get_redis", return_value=mock_redis):
            with patch.object(analytics_service.db, "execute") as mock_execute:
                mock_execute.return_value = mock_result

                result = await analytics_service.get_deal_funnel(organization_id=1)

        assert len(result["stages"]) == 4
        assert result["stages"][0]["stage"] == "qualification"
        assert result["stages"][0]["total_count"] == 7  # 5 new + 2 in_progress
        assert result["stages"][0]["conversion_rate"] == 100.0  # First stage

    @pytest.mark.asyncio
    async def test_invalidate_analytics_cache(self, test_session: AsyncSession):
        analytics_service = AnalyticsService(test_session)

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["deal_summary:1:30", "deal_summary:1:7"]
        mock_redis.delete = AsyncMock()

        with patch("app.services.analytics.cache_manager.get_redis", return_value=mock_redis):
            await analytics_service.invalidate_analytics_cache(organization_id=1)

        mock_redis.keys.assert_called_once_with("deal_summary:1:*")
        mock_redis.delete.assert_any_call("deal_summary:1:30", "deal_summary:1:7")
        mock_redis.delete.assert_any_call("deal_funnel:1")
