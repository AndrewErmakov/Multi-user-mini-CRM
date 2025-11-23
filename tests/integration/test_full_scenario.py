from datetime import datetime, timedelta

from fastapi.testclient import TestClient


class TestFullScenario:
    def test_full_user_journey(self, client: TestClient):
        """
        Полный сценарий:
        регистрация → создание организации → создание контакта → сделки → задачи → аналитика
        """

        # 1. Регистрация пользователя
        register_data = {
            "email": "owner@example.com",
            "password": "StrongPassword123",
            "name": "Alice Owner",
            "organization_name": "Acme Inc",
        }

        response = client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 200
        auth_data = response.json()
        assert "access_token" in auth_data
        access_token = auth_data["access_token"]

        # Получаем организации пользователя
        temp_headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/organizations/me", headers=temp_headers)
        assert response.status_code == 200
        organizations = response.json()
        assert len(organizations) > 0
        organization_id = organizations[0]["id"]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-Id": str(organization_id),
        }

        # 2. Создание контакта
        contact_data = {"name": "John Doe", "email": "john.doe@example.com", "phone": "+123456789"}

        response = client.post("/api/v1/contacts", json=contact_data, headers=headers)
        assert response.status_code == 200
        contact = response.json()
        contact_id = contact["id"]

        # 3. Создание сделки
        deal_data = {
            "contact_id": contact_id,
            "title": "Website redesign",
            "amount": 10000.0,
            "currency": "EUR",
        }

        response = client.post("/api/v1/deals", json=deal_data, headers=headers)
        assert response.status_code == 200
        deal = response.json()
        deal_id = deal["id"]

        # 4. Создание задачи
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S")
        task_data = {
            "deal_id": deal_id,
            "title": "Call client",
            "description": "Discuss proposal details",
            "due_date": future_date,
        }

        response = client.post("/api/v1/tasks", json=task_data, headers=headers)
        assert response.status_code == 200

        # 5. Получение аналитики
        response = client.get("/api/v1/analytics/deals/summary", headers=headers)
        assert response.status_code == 200
        summary = response.json()

        # Проверяем, что аналитика содержит ожидаемые поля
        assert "amount_by_status" in summary
        assert "average_won_amount" in summary
        assert "days_period" in summary
        assert "new_deals_last_n_days" in summary
        assert "status_counts" in summary

        # 6. Получение воронки продаж
        response = client.get("/api/v1/analytics/deals/funnel", headers=headers)
        assert response.status_code == 200
        funnel = response.json()

        assert "stages" in funnel
        assert "total_conversion" in funnel

    def test_authentication_flow(self, client: TestClient):
        """Тест потока аутентификации"""
        # Регистрация
        register_data = {
            "email": "auth_test@example.com",
            "password": "StrongPassword123",
            "name": "Auth Test User",
            "organization_name": "Auth Test Org",
        }

        response = client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 200
        auth_data = response.json()

        access_token = auth_data["access_token"]
        refresh_token = auth_data["refresh_token"]
        assert access_token is not None
        assert refresh_token is not None

        # Логин с теми же данными
        login_data = {"email": "auth_test@example.com", "password": "StrongPassword123"}

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        login_data = response.json()
        assert "access_token" in login_data

    def test_permission_checks(self, client: TestClient):
        """Тест проверок прав доступа"""
        # Создаем первого пользователя и организацию
        user1_data = {
            "email": "user1@example.com",
            "password": "Password123",
            "name": "User One",
            "organization_name": "Org One",
        }

        response = client.post("/api/v1/auth/register", json=user1_data)
        assert response.status_code == 200
        user1_token = response.json()["access_token"]

        # Получаем organization_id для первого пользователя
        temp_headers = {"Authorization": f"Bearer {user1_token}"}
        response = client.get("/api/v1/organizations/me", headers=temp_headers)
        assert response.status_code == 200
        user1_orgs = response.json()
        user1_org_id = user1_orgs[0]["id"]

        user1_headers = {
            "Authorization": f"Bearer {user1_token}",
            "X-Organization-Id": str(user1_org_id),
        }

        # Создаем контакт от первого пользователя
        contact_data = {"name": "User1 Contact", "email": "contact1@example.com"}

        response = client.post("/api/v1/contacts", json=contact_data, headers=user1_headers)
        assert response.status_code == 200
        user1_contact_id = response.json()["id"]

        # Создаем второго пользователя
        user2_data = {
            "email": "user2@example.com",
            "password": "Password123",
            "name": "User Two",
            "organization_name": "Org Two",
        }

        response = client.post("/api/v1/auth/register", json=user2_data)
        assert response.status_code == 200
        user2_token = response.json()["access_token"]

        # Получаем organization_id для второго пользователя
        temp_headers = {"Authorization": f"Bearer {user2_token}"}
        response = client.get("/api/v1/organizations/me", headers=temp_headers)
        assert response.status_code == 200
        user2_orgs = response.json()
        user2_org_id = user2_orgs[0]["id"]

        user2_headers = {
            "Authorization": f"Bearer {user2_token}",
            "X-Organization-Id": str(user2_org_id),
        }

        # Второй пользователь не должен видеть контакт первого пользователя
        response = client.delete(f"/api/v1/contacts/{user1_contact_id}", headers=user2_headers)
        assert response.status_code == 404
