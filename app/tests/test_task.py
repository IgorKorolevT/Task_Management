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

        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["pages"] == 1

        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Task 1"
        assert data["items"][1]["title"] == "Task 2"

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


class TestTaskFiltering:
    @pytest.mark.asyncio
    async def test_search_tasks(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        headers = {
            "Authorization": f"Bearer {token}",
        }

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Python Backend",
                "description": "FastAPI project",
                "deadline": deadline,
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Frontend task",
                "description": "React project",
                "deadline": deadline,
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks?search=Python",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["title"] == "Python Backend"

    @pytest.mark.asyncio
    async def test_search_tasks_by_description(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        headers = {
            "Authorization": f"Bearer {token}",
        }

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Some task",
                "description": "Unique FastAPI description",
                "deadline": deadline,
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks?search=FastAPI",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_filter_by_status(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        headers = {
            "Authorization": f"Bearer {token}",
        }

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Status task",
                "deadline": deadline,
            },
            headers=headers,
        )

        task_id = response.json()["id"]

        await client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "In Progress"},
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks?status=In%20Progress",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["status"] == "In Progress"

    @pytest.mark.asyncio
    async def test_filter_by_priority(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        headers = {
            "Authorization": f"Bearer {token}",
        }

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "High task",
                "priority": "High",
                "deadline": deadline,
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Low task",
                "priority": "Low",
                "deadline": deadline,
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks?priority=High",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["priority"] == "High"

    @pytest.mark.asyncio
    async def test_default_sorting(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Low task",
                "priority": "Low",
                "deadline": (
                        now + timedelta(days=1)
                ).isoformat(),
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "High later",
                "priority": "High",
                "deadline": (
                        now + timedelta(days=3)
                ).isoformat(),
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "High sooner",
                "priority": "High",
                "deadline": (
                        now + timedelta(days=1)
                ).isoformat(),
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Medium task",
                "priority": "Medium",
                "deadline": (
                        now + timedelta(hours=1)
                ).isoformat(),
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks",
            headers=headers,
        )

        assert response.status_code == 200

        titles = [
            item["title"]
            for item in response.json()["items"]
        ]

        assert titles == [
            "High sooner",
            "High later",
            "Medium task",
            "Low task",
        ]

    @pytest.mark.asyncio
    async def test_task_pagination(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        headers = {
            "Authorization": f"Bearer {token}",
        }

        for i in range(5):
            await client.post(
                "/api/v1/tasks",
                json={
                    "title": f"Task {i}",
                    "deadline": deadline,
                },
                headers=headers,
            )

        response = await client.get(
            "/api/v1/tasks?page=2&page_size=2",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 5
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert data["pages"] == 3
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_filter_by_assignee(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        headers = {
            "Authorization": f"Bearer {token}",
        }

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Assigned task",
                "assignee_id": test_user.id,
                "deadline": deadline,
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Unassigned task",
                "deadline": deadline,
            },
            headers=headers,
        )

        response = await client.get(
            f"/api/v1/tasks?assignee_id={test_user.id}",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["title"] == "Assigned task"
        assert data["items"][0]["assignee_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_filter_by_deadline(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        early_deadline = now + timedelta(days=1)
        late_deadline = now + timedelta(days=5)

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Early task",
                "deadline": early_deadline.isoformat(),
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Late task",
                "deadline": late_deadline.isoformat(),
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "deadline_from": (
                        now + timedelta(days=4)
                ).isoformat(),
            },
            headers=headers,
        )

        print(response.json())

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["title"] == "Late task"

    @pytest.mark.asyncio
    async def test_sort_by_deadline(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Late task",
                "deadline": (
                        now + timedelta(days=3)
                ).isoformat(),
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Early task",
                "deadline": (
                        now + timedelta(days=1)
                ).isoformat(),
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks?sort_by=deadline&sort_order=asc",
            headers=headers,
        )

        assert response.status_code == 200

        titles = [
            item["title"]
            for item in response.json()["items"]
        ]

        assert titles == [
            "Early task",
            "Late task",
        ]

    @pytest.mark.asyncio
    async def test_sort_by_created_at(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "First task",
                "deadline": deadline,
            },
            headers=headers,
        )

        await client.post(
            "/api/v1/tasks",
            json={
                "title": "Second task",
                "deadline": deadline,
            },
            headers=headers,
        )

        response = await client.get(
            "/api/v1/tasks?sort_by=created_at&sort_order=asc",
            headers=headers,
        )

        titles = [
            item["title"]
            for item in response.json()["items"]
        ]

        assert titles == [
            "First task",
            "Second task",
        ]

    @pytest.mark.asyncio
    async def test_sort_by_priority(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        deadline = (
                datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()

        for title, priority in [
            ("Low task", "Low"),
            ("High task", "High"),
            ("Medium task", "Medium"),
        ]:
            await client.post(
                "/api/v1/tasks",
                json={
                    "title": title,
                    "priority": priority,
                    "deadline": deadline,
                },
                headers=headers,
            )

        response = await client.get(
            "/api/v1/tasks?sort_by=priority&sort_order=asc",
            headers=headers,
        )

        assert response.status_code == 200

        priorities = [
            item["priority"]
            for item in response.json()["items"]
        ]

        assert priorities == [
            "High",
            "Medium",
            "Low",
        ]

    @pytest.mark.asyncio
    async def test_combined_search_filter_sort_and_pagination(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        # --------------------------------------------------
        # Create tasks
        # --------------------------------------------------

        tasks = [
            {
                "title": "Python API High 1",
                "description": "FastAPI backend project",
                "priority": "High",
                "deadline": (
                        now + timedelta(days=3)
                ).isoformat(),
            },
            {
                "title": "Python API High 2",
                "description": "FastAPI authentication",
                "priority": "High",
                "deadline": (
                        now + timedelta(days=1)
                ).isoformat(),
            },
            {
                "title": "Python API Medium",
                "description": "FastAPI database",
                "priority": "Medium",
                "deadline": (
                        now + timedelta(days=2)
                ).isoformat(),
            },
            {
                "title": "Python API Low",
                "description": "FastAPI frontend integration",
                "priority": "Low",
                "deadline": (
                        now + timedelta(days=1)
                ).isoformat(),
            },
            {
                "title": "Django task",
                "description": "Django backend",
                "priority": "High",
                "deadline": (
                        now + timedelta(days=1)
                ).isoformat(),
            },
        ]

        for task in tasks:
            response = await client.post(
                "/api/v1/tasks",
                json=task,
                headers=headers,
            )

            assert response.status_code == 201

        # --------------------------------------------------
        # Combined query:
        #
        # search=Python
        # priority=High
        # sort_by=deadline
        # sort_order=asc
        # page=1
        # page_size=1
        # --------------------------------------------------

        response = await client.get(
            "/api/v1/tasks",
            params={
                "search": "Python",
                "priority": "High",
                "sort_by": "deadline",
                "sort_order": "asc",
                "page": 1,
                "page_size": 1,
            },
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        # --------------------------------------------------
        # Only 2 tasks should match:
        #
        # Python API High 1
        # Python API High 2
        # --------------------------------------------------

        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 1
        assert data["pages"] == 2

        assert len(data["items"]) == 1

        assert data["items"][0]["title"] == "Python API High 2"
        assert data["items"][0]["priority"] == "High"

        # --------------------------------------------------
        # Check second page
        # --------------------------------------------------

        response = await client.get(
            "/api/v1/tasks",
            params={
                "search": "Python",
                "priority": "High",
                "sort_by": "deadline",
                "sort_order": "asc",
                "page": 2,
                "page_size": 1,
            },
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 2
        assert data["page"] == 2
        assert data["page_size"] == 1
        assert data["pages"] == 2

        assert len(data["items"]) == 1

        assert data["items"][0]["title"] == "Python API High 1"
        assert data["items"][0]["priority"] == "High"


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
