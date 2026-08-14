import pytest
from datetime import datetime, timedelta, timezone


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


async def create_task(client, user):
    token = await get_token(client, user)

    deadline = (
        datetime.now(timezone.utc) + timedelta(days=2)
    ).isoformat()

    response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Task for comments",
            "description": "Test task",
            "priority": "Medium",
            "deadline": deadline,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    return response.json(), token


class TestComment:

    @pytest.mark.asyncio
    async def test_create_comment(
        self,
        client,
        test_user,
    ):
        task, token = await create_task(
            client,
            test_user,
        )

        response = await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={
                "content": "This is a test comment",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["task_id"] == task["id"]
        assert data["author_id"] == test_user.id
        assert data["content"] == "This is a test comment"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_comments(
        self,
        client,
        test_user,
    ):
        task, token = await create_task(
            client,
            test_user,
        )

        await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={
                "content": "First comment",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={
                "content": "Second comment",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        response = await client.get(
            f"/api/v1/tasks/{task['id']}/comments",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2
        assert data[0]["content"] == "First comment"
        assert data[1]["content"] == "Second comment"

    @pytest.mark.asyncio
    async def test_create_comment_task_not_found(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        response = await client.post(
            "/api/v1/tasks/999999/comments",
            json={
                "content": "Comment",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    @pytest.mark.asyncio
    async def test_get_comments_task_not_found(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        response = await client.get(
            "/api/v1/tasks/999999/comments",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    @pytest.mark.asyncio
    async def test_create_empty_comment(
        self,
        client,
        test_user,
    ):
        task, token = await create_task(
            client,
            test_user,
        )

        response = await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={
                "content": "",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_comments_require_authentication(
        self,
        client,
        test_user,
    ):
        task, _ = await create_task(
            client,
            test_user,
        )

        response = await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={
                "content": "Unauthorized comment",
            },
        )

        assert response.status_code == 401

        response = await client.get(
            f"/api/v1/tasks/{task['id']}/comments",
        )

        assert response.status_code == 401