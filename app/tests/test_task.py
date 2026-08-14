import pytest
from datetime import datetime, timedelta, timezone
from app.task.models import TaskPriority, TaskStatus


class TestTaskCRUD:

    @pytest.mark.asyncio
    async def test_create_task(self, client, test_user):
        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        token = await get_token(client, test_user)

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Test task",
                "description": "Task description",
                "priority": "High",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["title"] == "Test task"
        assert data["description"] == "Task description"
        assert data["priority"] == TaskPriority.HIGH.value
        assert data["status"] == TaskStatus.BACKLOG.value
        assert data["author_id"] == test_user.id
        assert data["assignee_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_task(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Get task",
                "description": "Description",
                "priority": "Medium",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        task_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert response.json()["title"] == "Get task"

    @pytest.mark.asyncio
    async def test_get_tasks(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Task 1",
                "priority": "High",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Task 2",
                "priority": "Low",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        response = await client.get(
            "/api/v1/tasks",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"

    @pytest.mark.asyncio
    async def test_update_task(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Old title",
                "priority": "Low",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        task_id = create_response.json()["id"]

        response = await client.put(
            f"/api/v1/tasks/{task_id}",
            json={
                "title": "Updated title",
                "description": "Updated description",
                "priority": "High",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["title"] == "Updated title"
        assert data["description"] == "Updated description"
        assert data["priority"] == "High"

    @pytest.mark.asyncio
    async def test_delete_task(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Task to delete",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        task_id = create_response.json()["id"]

        response = await client.delete(
            f"/api/v1/tasks/{task_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 204

        response = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_task_with_past_deadline(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) - timedelta(days=1)
        ).isoformat()

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Invalid task",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Deadline must be in the future"
        )

    @pytest.mark.asyncio
    async def test_put_cannot_change_status(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Status test",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        task_id = create_response.json()["id"]

        response = await client.put(
            f"/api/v1/tasks/{task_id}",
            json={
                "title": "Updated",
                "status": "In Progress",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Backlog"

    @pytest.mark.asyncio
    async def test_change_status(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Status test",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        task_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={
                "status": "In Progress",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "In Progress"

    @pytest.mark.asyncio
    async def test_cannot_move_status_back(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Status transition",
                "deadline": deadline,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        task_id = create_response.json()["id"]

        await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "In Progress"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "Backlog"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_complete_without_assignee(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "No assignee",
                "deadline": deadline,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        task_id = create_response.json()["id"]

        await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "In Progress"},
            headers={"Authorization": f"Bearer {token}"},
        )

        await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "Review"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "Done"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Task must have an assignee before completion"
        )

    @pytest.mark.asyncio
    async def test_done_task_cannot_be_updated(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Done task",
                "deadline": deadline,
                "assignee_id": test_user.id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        task_id = create_response.json()["id"]

        await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "In Progress"},
            headers={"Authorization": f"Bearer {token}"},
        )

        await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "Review"},
            headers={"Authorization": f"Bearer {token}"},
        )

        await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "Done"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.put(
            f"/api/v1/tasks/{task_id}",
            json={
                "title": "Should fail",
                "deadline": deadline,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Task cannot be edited in its current status"
        )

    @pytest.mark.asyncio
    async def test_status_transition_must_follow_order(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        create_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Invalid transition",
                "deadline": deadline,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        task_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "Done"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400


@pytest.mark.asyncio
async def get_token(client, user):
    response = await client.post(
        "/api/v1/users/login",
        json={
            "username": user.username,
            "password": "testpass123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]
