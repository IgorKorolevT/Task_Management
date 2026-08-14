import pytest
from datetime import datetime, timedelta, timezone
from app.task.models import TaskPriority, TaskStatus
from app.task.dao import TaskDAO

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


class TestTaskAdditionalEndpoints:

    @pytest.mark.asyncio
    async def test_get_overdue_tasks(
            self,
            client,
            test_user,
            test_db,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        # -------------------------------------------------
        # Create task that will become overdue
        # -------------------------------------------------

        overdue_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Overdue task",
                "deadline": (
                    now + timedelta(days=2)
                ).isoformat(),
            },
            headers=headers,
        )

        assert overdue_response.status_code == 201

        overdue_task_id = overdue_response.json()["id"]

        # Make deadline overdue directly in DB.
        async with test_db() as db:
            overdue_task = await TaskDAO.get_by_id(
                db,
                overdue_task_id,
            )

            assert overdue_task is not None

            overdue_task.deadline = (
                now - timedelta(days=1)
            )

            await db.commit()

        # -------------------------------------------------
        # Create active task with future deadline
        # -------------------------------------------------

        active_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Active task",
                "deadline": (
                    now + timedelta(days=2)
                ).isoformat(),
            },
            headers=headers,
        )

        assert active_response.status_code == 201

        # -------------------------------------------------
        # Get overdue tasks
        # -------------------------------------------------

        response = await client.get(
            "/api/v1/tasks/overdue",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        # Only one task should be overdue.
        assert len(data) == 1

        assert data[0]["id"] == overdue_task_id
        assert data[0]["title"] == "Overdue task"

        # Active task must not be returned.
        assert all(
            task["title"] != "Active task"
            for task in data
        )

    @pytest.mark.asyncio
    async def test_overdue_done_and_cancelled_tasks_are_not_returned(
            self,
            client,
            test_user,
            test_db,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        # -------------------------------------------------
        # Create overdue active task
        # -------------------------------------------------

        overdue_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Overdue active",
                "deadline": (
                    now + timedelta(days=2)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers=headers,
        )

        assert overdue_response.status_code == 201

        overdue_task_id = overdue_response.json()["id"]

        async with test_db() as db:
            overdue_task = await TaskDAO.get_by_id(
                db,
                overdue_task_id,
            )

            assert overdue_task is not None

            overdue_task.deadline = (
                now - timedelta(days=1)
            )

            await db.commit()

        # -------------------------------------------------
        # Create task that will become Done
        # -------------------------------------------------

        done_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Overdue done",
                "deadline": (
                    now + timedelta(days=2)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers=headers,
        )

        assert done_response.status_code == 201

        done_task_id = done_response.json()["id"]

        # Backlog -> In Progress
        response = await client.patch(
            f"/api/v1/tasks/{done_task_id}/status",
            json={
                "status": "In Progress",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # In Progress -> Review
        response = await client.patch(
            f"/api/v1/tasks/{done_task_id}/status",
            json={
                "status": "Review",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # Review -> Done
        response = await client.patch(
            f"/api/v1/tasks/{done_task_id}/status",
            json={
                "status": "Done",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # -------------------------------------------------
        # Create task that will become Cancelled
        # -------------------------------------------------

        cancelled_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Overdue cancelled",
                "deadline": (
                    now + timedelta(days=2)
                ).isoformat(),
            },
            headers=headers,
        )

        assert cancelled_response.status_code == 201

        cancelled_task_id = (
            cancelled_response.json()["id"]
        )

        # Backlog -> Cancelled
        response = await client.patch(
            f"/api/v1/tasks/{cancelled_task_id}/status",
            json={
                "status": "Cancelled",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # -------------------------------------------------
        # Make Done and Cancelled tasks overdue
        # -------------------------------------------------

        async with test_db() as db:
            done_task = await TaskDAO.get_by_id(
                db,
                done_task_id,
            )

            cancelled_task = await TaskDAO.get_by_id(
                db,
                cancelled_task_id,
            )

            assert done_task is not None
            assert cancelled_task is not None

            done_task.deadline = (
                now - timedelta(days=1)
            )

            cancelled_task.deadline = (
                now - timedelta(days=1)
            )

            await db.commit()

        # -------------------------------------------------
        # Get overdue tasks
        # -------------------------------------------------

        response = await client.get(
            "/api/v1/tasks/overdue",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        task_ids = {
            task["id"]
            for task in data
        }

        # Active overdue task must be returned.
        assert overdue_task_id in task_ids

        # Done overdue task must NOT be returned.
        assert done_task_id not in task_ids

        # Cancelled overdue task must NOT be returned.
        assert cancelled_task_id not in task_ids

        # Every returned task should be the active overdue task.
        for task in data:
            assert task["title"] == "Overdue active"


class TestTaskStatistics:

    @pytest.mark.asyncio
    async def test_task_statistics(
            self,
            client,
            test_user,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        # -------------------------------------------------
        # High / Backlog
        # -------------------------------------------------

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "High task",
                "priority": "High",
                "deadline": deadline,
            },
            headers=headers,
        )

        assert response.status_code == 201

        # -------------------------------------------------
        # Medium / Backlog
        # -------------------------------------------------

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Medium task",
                "priority": "Medium",
                "deadline": deadline,
            },
            headers=headers,
        )

        assert response.status_code == 201

        # -------------------------------------------------
        # Low / Backlog
        # -------------------------------------------------

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Low task",
                "priority": "Low",
                "deadline": deadline,
            },
            headers=headers,
        )

        assert response.status_code == 201

        # -------------------------------------------------
        # Get statistics
        # -------------------------------------------------

        response = await client.get(
            "/api/v1/tasks/statistics",
            headers=headers,
        )

        assert response.status_code == 200

        data = response.json()

        # -------------------------------------------------
        # Total
        # -------------------------------------------------

        assert data["total"] == 3

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        assert data["by_status"]["Backlog"] == 3
        assert data["by_status"]["In Progress"] == 0
        assert data["by_status"]["Review"] == 0
        assert data["by_status"]["Done"] == 0
        assert data["by_status"]["Cancelled"] == 0

        # -------------------------------------------------
        # Priority
        # -------------------------------------------------

        assert data["by_priority"]["High"] == 1
        assert data["by_priority"]["Medium"] == 1
        assert data["by_priority"]["Low"] == 1

        # -------------------------------------------------
        # Active
        # -------------------------------------------------

        assert data["active"] == 3

        # -------------------------------------------------
        # Overdue
        # -------------------------------------------------

        assert data["overdue"] == 0

class TestTaskBackgroundWorker:

    @pytest.mark.asyncio
    async def test_overdue_task_is_cancelled(
            self,
            client,
            test_user,
            test_db,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        # -------------------------------------------------
        # Create task
        # -------------------------------------------------

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Overdue task",
                "deadline": (
                    now + timedelta(days=1)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers=headers,
        )

        assert response.status_code == 201

        task_id = response.json()["id"]

        # -------------------------------------------------
        # Make task overdue directly in DB
        # -------------------------------------------------

        async with test_db() as db:
            task = await TaskDAO.get_by_id(
                db,
                task_id,
            )

            assert task is not None

            task.deadline = (
                now - timedelta(days=1)
            )

            await db.commit()

        # -------------------------------------------------
        # Run background processing manually
        # -------------------------------------------------

        from app.task.background import process_overdue_tasks

        async with test_db() as db:
            await process_overdue_tasks(db)

        # -------------------------------------------------
        # Check status
        # -------------------------------------------------

        async with test_db() as db:
            task = await TaskDAO.get_by_id(
                db,
                task_id,
            )

            assert task is not None
            assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_done_and_cancelled_tasks_are_not_changed(
            self,
            client,
            test_user,
            test_db,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        # -------------------------------------------------
        # DONE task
        # -------------------------------------------------

        done_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Done overdue task",
                "deadline": (
                    now + timedelta(days=1)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers=headers,
        )

        assert done_response.status_code == 201

        done_task_id = done_response.json()["id"]

        # Backlog -> In Progress
        response = await client.patch(
            f"/api/v1/tasks/{done_task_id}/status",
            json={
                "status": "In Progress",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # In Progress -> Review
        response = await client.patch(
            f"/api/v1/tasks/{done_task_id}/status",
            json={
                "status": "Review",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # Review -> Done
        response = await client.patch(
            f"/api/v1/tasks/{done_task_id}/status",
            json={
                "status": "Done",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # -------------------------------------------------
        # CANCELLED task
        # -------------------------------------------------

        cancelled_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Cancelled overdue task",
                "deadline": (
                    now + timedelta(days=1)
                ).isoformat(),
            },
            headers=headers,
        )

        assert cancelled_response.status_code == 201

        cancelled_task_id = (
            cancelled_response.json()["id"]
        )

        # Backlog -> Cancelled
        response = await client.patch(
            f"/api/v1/tasks/{cancelled_task_id}/status",
            json={
                "status": "Cancelled",
            },
            headers=headers,
        )

        assert response.status_code == 200

        # -------------------------------------------------
        # Make both tasks overdue
        # -------------------------------------------------

        async with test_db() as db:
            done_task = await TaskDAO.get_by_id(
                db,
                done_task_id,
            )

            cancelled_task = await TaskDAO.get_by_id(
                db,
                cancelled_task_id,
            )

            assert done_task is not None
            assert cancelled_task is not None

            done_task.deadline = (
                now - timedelta(days=1)
            )

            cancelled_task.deadline = (
                now - timedelta(days=1)
            )

            await db.commit()

        # -------------------------------------------------
        # Run background processing
        # -------------------------------------------------

        from app.task.background import process_overdue_tasks

        async with test_db() as db:
            await process_overdue_tasks(db)

        # -------------------------------------------------
        # Check statuses
        # -------------------------------------------------

        async with test_db() as db:
            done_task = await TaskDAO.get_by_id(
                db,
                done_task_id,
            )

            cancelled_task = await TaskDAO.get_by_id(
                db,
                cancelled_task_id,
            )

            assert done_task is not None
            assert cancelled_task is not None

            assert done_task.status == TaskStatus.DONE
            assert cancelled_task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_future_task_is_not_cancelled(
            self,
            client,
            test_user,
            test_db,
    ):
        token = await get_token(client, test_user)

        headers = {
            "Authorization": f"Bearer {token}",
        }

        now = datetime.now(timezone.utc)

        # -------------------------------------------------
        # Create future task
        # -------------------------------------------------

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Future task",
                "deadline": (
                    now + timedelta(days=5)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers=headers,
        )

        assert response.status_code == 201

        task_id = response.json()["id"]

        # -------------------------------------------------
        # Run background processing
        # -------------------------------------------------

        from app.task.background import process_overdue_tasks

        async with test_db() as db:
            await process_overdue_tasks(db)

        # -------------------------------------------------
        # Task must remain Backlog
        # -------------------------------------------------

        async with test_db() as db:
            task = await TaskDAO.get_by_id(
                db,
                task_id,
            )

            assert task is not None
            assert task.status == TaskStatus.BACKLOG
