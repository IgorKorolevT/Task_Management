from datetime import datetime, timedelta, timezone

import pytest

from app.task.dao import TaskDAO
from app.task.models import TaskStatus
from app.task.background import process_overdue_tasks


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


class TestTaskBackground:

    @pytest.mark.asyncio
    async def test_overdue_task_is_cancelled(
        self,
        client,
        test_user,
        test_db,
    ):
        token = await get_token(
            client,
            test_user,
        )

        now = datetime.now(timezone.utc)

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Overdue task",
                "deadline": (
                    now + timedelta(days=1)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 201

        task_id = response.json()["id"]

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

        async with test_db() as db:
            cancelled_count = (
                await process_overdue_tasks(db)
            )

        assert cancelled_count == 1

        async with test_db() as db:
            task = await TaskDAO.get_by_id(
                db,
                task_id,
            )

            assert task is not None
            assert task.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_done_and_cancelled_are_not_changed(
        self,
        client,
        test_user,
        test_db,
    ):
        token = await get_token(
            client,
            test_user,
        )

        now = datetime.now(timezone.utc)

        done_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Done task",
                "deadline": (
                    now + timedelta(days=1)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert done_response.status_code == 201

        done_task_id = done_response.json()["id"]

        for next_status in (
            "In Progress",
            "Review",
            "Done",
        ):
            response = await client.patch(
                f"/api/v1/tasks/{done_task_id}/status",
                json={
                    "status": next_status,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )

            assert response.status_code == 200

        cancelled_response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Cancelled task",
                "deadline": (
                    now + timedelta(days=1)
                ).isoformat(),
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert cancelled_response.status_code == 201

        cancelled_task_id = (
            cancelled_response.json()["id"]
        )

        response = await client.patch(
            f"/api/v1/tasks/{cancelled_task_id}/status",
            json={
                "status": "Cancelled",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

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

        async with test_db() as db:
            cancelled_count = (
                await process_overdue_tasks(db)
            )

        assert cancelled_count == 0

        async with test_db() as db:
            done_task = await TaskDAO.get_by_id(
                db,
                done_task_id,
            )

            cancelled_task = await TaskDAO.get_by_id(
                db,
                cancelled_task_id,
            )

            assert done_task.status == TaskStatus.DONE
            assert (
                cancelled_task.status
                == TaskStatus.CANCELLED
            )

    @pytest.mark.asyncio
    async def test_future_task_is_not_cancelled(
        self,
        client,
        test_user,
        test_db,
    ):
        token = await get_token(
            client,
            test_user,
        )

        response = await client.post(
            "/api/v1/tasks",
            json={
                "title": "Future task",
                "deadline": (
                    datetime.now(timezone.utc)
                    + timedelta(days=5)
                ).isoformat(),
                "assignee_id": test_user.id,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 201

        task_id = response.json()["id"]

        async with test_db() as db:
            cancelled_count = (
                await process_overdue_tasks(db)
            )

        assert cancelled_count == 0

        async with test_db() as db:
            task = await TaskDAO.get_by_id(
                db,
                task_id,
            )

            assert task is not None
            assert task.status == TaskStatus.BACKLOG