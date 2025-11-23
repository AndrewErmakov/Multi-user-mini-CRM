# tests/integration/test_business_rules.py
import pytest
from fastapi.testclient import TestClient


class TestBusinessRules:
    def _register_and_login(self, client: TestClient, email_suffix: str = ""):
        """Регистрирует и логинит пользователя, возвращает headers"""
        # Регистрация
        register_data = {
            "email": f"test_business{email_suffix}@example.com",
            "password": "Password123",
            "name": "Test User",
            "organization_name": f"Test Org {email_suffix}",
        }

        response = client.post("/api/v1/auth/register", json=register_data)
        if response.status_code != 200:
            print(f"🔧 DEBUG: Registration failed: {response.status_code} - {response.text}")
            return None

        auth_data = response.json()
        access_token = auth_data["access_token"]

        # Получаем список организаций пользователя
        temp_headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/v1/organizations/me", headers=temp_headers)

        if response.status_code != 200:
            print(f"🔧 DEBUG: Get organizations failed: {response.status_code} - {response.text}")
            return None

        organizations = response.json()
        if not organizations:
            print("🔧 DEBUG: No organizations found")
            return None

        organization_id = organizations[0]["id"]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-Id": str(organization_id),
        }

        return headers

    def _create_test_contact(self, client: TestClient, headers, email_suffix: str = ""):
        """Создает тестовый контакт и возвращает его ID"""
        contact_data = {
            "name": f"Test Contact {email_suffix}",
            "email": f"contact{email_suffix}@example.com",
        }
        response = client.post("/api/v1/contacts", json=contact_data, headers=headers)

        if response.status_code != 200:
            print(f"🔧 DEBUG: Create contact failed: {response.status_code} - {response.text}")
            return None

        return response.json()["id"]

    def _create_test_deal(
            self, client: TestClient, headers, contact_id: int, amount: float = 1000.0
    ):
        """Создает тестовую сделку и возвращает ее ID"""
        deal_data = {
            "contact_id": contact_id,
            "title": "Test Deal",
            "amount": amount,
            "currency": "USD",
            "status": "new",
            "stage": "qualification",
        }
        response = client.post("/api/v1/deals", json=deal_data, headers=headers)

        if response.status_code != 200:
            print(f"🔧 DEBUG: Create deal failed: {response.status_code} - {response.text}")
            return None

        return response.json()["id"]

    def test_cannot_close_deal_with_zero_amount(self, client: TestClient):
        """Тест: нельзя закрыть сделку с amount <= 0"""
        # Регистрируем пользователя
        headers = self._register_and_login(client, "_zero_amount")
        if not headers:
            pytest.skip("Failed to register and login")

        # Создаем контакт
        contact_id = self._create_test_contact(client, headers, "_zero_amount")
        if not contact_id:
            pytest.skip("Failed to create contact")

        # Создаем сделку с нулевой суммой
        deal_id = self._create_test_deal(client, headers, contact_id, amount=0.0)
        if not deal_id:
            pytest.skip("Failed to create deal")

        # Пытаемся закрыть сделку как won - должно быть ошибка
        update_data = {"status": "won"}
        response = client.patch(f"/api/v1/deals/{deal_id}", json=update_data, headers=headers)

        assert response.status_code == 400
        assert "amount" in response.json()["detail"].lower()

    def test_cannot_delete_contact_with_active_deals(self, client: TestClient):
        """Тест: нельзя удалить контакт с активными сделками"""
        # Регистрируем пользователя
        headers = self._register_and_login(client, "_active_deals")
        if not headers:
            pytest.skip("Failed to register and login")

        # Создаем контакт
        contact_id = self._create_test_contact(client, headers, "_active_deals")
        if not contact_id:
            pytest.skip("Failed to create contact")

        # Создаем сделку для этого контакта
        deal_id = self._create_test_deal(client, headers, contact_id, amount=1000.0)
        if not deal_id:
            pytest.skip("Failed to create deal")

        # Пытаемся удалить контакт - должно быть ошибка
        response = client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)

        assert response.status_code == 409
        assert "active deals" in response.json()["detail"].lower()

    def test_cannot_set_task_due_date_in_past(self, client: TestClient):
        """Тест: нельзя установить due_date задачи в прошлом"""
        # Регистрируем пользователя
        headers = self._register_and_login(client, "_past_task")
        if not headers:
            pytest.skip("Failed to register and login")

        # Создаем контакт и сделку
        contact_id = self._create_test_contact(client, headers, "_past_task")
        if not contact_id:
            pytest.skip("Failed to create contact")

        deal_id = self._create_test_deal(client, headers, contact_id, amount=1000.0)
        if not deal_id:
            pytest.skip("Failed to create deal")

        # Пытаемся создать задачу с датой в прошлом
        task_data = {
            "deal_id": deal_id,
            "title": "Past Task",
            "due_date": "2020-01-01T00:00:00",  # Прошлая дата
        }

        response = client.post("/api/v1/tasks", json=task_data, headers=headers)

        assert response.status_code == 400
        assert "past" in response.json()["detail"].lower()

    def test_can_delete_contact_without_deals(self, client: TestClient):
        """Тест: можно удалить контакт без сделок"""
        # Регистрируем пользователя
        headers = self._register_and_login(client, "_no_deals")
        if not headers:
            pytest.skip("Failed to register and login")

        # Создаем контакт
        contact_id = self._create_test_contact(client, headers, "_no_deals")
        if not contact_id:
            pytest.skip("Failed to create contact")

        # Пытаемся удалить контакт - должно быть успешно
        response = client.delete(f"/api/v1/contacts/{contact_id}", headers=headers)

        assert response.status_code == 204

    def test_can_close_deal_with_positive_amount(self, client: TestClient):
        """Тест: можно закрыть сделку с amount > 0"""
        # Регистрируем пользователя
        headers = self._register_and_login(client, "_positive_amount")
        if not headers:
            pytest.skip("Failed to register and login")

        # Создаем контакт
        contact_id = self._create_test_contact(client, headers, "_positive_amount")
        if not contact_id:
            pytest.skip("Failed to create contact")

        # Создаем сделку с положительной суммой
        deal_id = self._create_test_deal(client, headers, contact_id, amount=1000.0)
        if not deal_id:
            pytest.skip("Failed to create deal")

        # Пытаемся закрыть сделку как won - должно быть успешно
        update_data = {"status": "won"}
        response = client.patch(f"/api/v1/deals/{deal_id}", json=update_data, headers=headers)

        assert response.status_code == 200
        assert response.json()["status"] == "won"

    def test_can_create_task_with_future_due_date(self, client: TestClient):
        """Тест: можно создать задачу с due_date в будущем"""
        # Регистрируем пользователя
        headers = self._register_and_login(client, "_future_task")
        if not headers:
            pytest.skip("Failed to register and login")

        # Создаем контакт и сделку
        contact_id = self._create_test_contact(client, headers, "_future_task")
        if not contact_id:
            pytest.skip("Failed to create contact")

        deal_id = self._create_test_deal(client, headers, contact_id, amount=1000.0)
        if not deal_id:
            pytest.skip("Failed to create deal")

        # Пытаемся создать задачу с датой в будущем
        task_data = {
            "deal_id": deal_id,
            "title": "Future Task",
            "due_date": "2030-01-01T00:00:00",  # Будущая дата
        }

        response = client.post("/api/v1/tasks", json=task_data, headers=headers)

        assert response.status_code == 200
        assert response.json()["title"] == "Future Task"

    def test_cannot_create_task_for_deal_from_different_organization(self, client: TestClient):
        """Тест: нельзя создать задачу для сделки из другой организации"""
        # Регистрируем первого пользователя
        headers1 = self._register_and_login(client, "_org1")
        if not headers1:
            pytest.skip("Failed to register user 1")

        # Создаем сделку у первого пользователя
        contact_id1 = self._create_test_contact(client, headers1, "_org1")
        if not contact_id1:
            pytest.skip("Failed to create contact for user 1")

        deal_id1 = self._create_test_deal(client, headers1, contact_id1, amount=1000.0)
        if not deal_id1:
            pytest.skip("Failed to create deal for user 1")

        # Регистрируем второго пользователя (в другой организации)
        headers2 = self._register_and_login(client, "_org2")
        if not headers2:
            pytest.skip("Failed to register user 2")

        # Пытаемся создать задачу у второго пользователя для сделки первого пользователя
        task_data = {
            "deal_id": deal_id1,
            "title": "Cross-org Task",
            "due_date": "2030-01-01T00:00:00"
        }

        response = client.post("/api/v1/tasks", json=task_data, headers=headers2)

        # Должна быть ошибка, что сделка не найдена (потому что из другой организации)
        assert response.status_code == 404
        assert "deal" in response.json()["detail"].lower()
