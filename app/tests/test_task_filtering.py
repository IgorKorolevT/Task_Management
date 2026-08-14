from datetime import datetime, timedelta, timezone

import pytest


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


async def create_task(
    client,
    token,
    title,
    deadline,
    priority="Medium",
    description=None,
    assignee_id=None,
):
    response = await client.post(
        "/api/v1/tasks",
        json={
            "title": title,
            "description": description,
            "priority": priority,
            "assignee_id": assignee_id,
            "deadline": deadline,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    return response.json()


class TestTaskFiltering:

    @pytest.mark.asyncio
    async def test_search_by_title(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        await create_task(
            client,
            token,
            title="Python Backend",
            description="Backend project",
            deadline=deadline,
        )

        await create_task(
            client,
            token,
            title="Frontend",
            description="React project",
            deadline=deadline,
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "search": "Python",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Python Backend"

    @pytest.mark.asyncio
    async def test_search_by_description(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        await create_task(
            client,
            token,
            title="Backend task",
            description="FastAPI development",
            deadline=deadline,
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "search": "FastAPI",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["title"] == "Backend task"

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        task = await create_task(
            client,
            token,
            title="In progress",
            deadline=deadline,
        )

        await client.patch(
            f"/api/v1/tasks/{task['id']}/status",
            json={
                "status": "In Progress",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "status": "In Progress",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
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
        token = await get_token(
            client,
            test_user,
        )

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        await create_task(
            client,
            token,
            title="High",
            priority="High",
            deadline=deadline,
        )

        await create_task(
            client,
            token,
            title="Low",
            priority="Low",
            deadline=deadline,
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "priority": "High",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["priority"] == "High"

    @pytest.mark.asyncio
    async def test_filter_by_assignee(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        await create_task(
            client,
            token,
            title="Assigned",
            assignee_id=test_user.id,
            deadline=deadline,
        )

        await create_task(
            client,
            token,
            title="Unassigned",
            deadline=deadline,
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "assignee_id": test_user.id,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["title"] == "Assigned"

    @pytest.mark.asyncio
    async def test_default_sorting(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        now = datetime.now(timezone.utc)

        await create_task(
            client,
            token,
            title="Low",
            priority="Low",
            deadline=(
                now + timedelta(days=1)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="High later",
            priority="High",
            deadline=(
                now + timedelta(days=3)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="High sooner",
            priority="High",
            deadline=(
                now + timedelta(days=1)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="Medium",
            priority="Medium",
            deadline=(
                now + timedelta(hours=1)
            ).isoformat(),
        )

        response = await client.get(
            "/api/v1/tasks",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        titles = [
            item["title"]
            for item in response.json()["items"]
        ]

        assert titles == [
            "High sooner",
            "High later",
            "Medium",
            "Low",
        ]

    @pytest.mark.asyncio
    async def test_sort_by_deadline_desc(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        now = datetime.now(timezone.utc)

        await create_task(
            client,
            token,
            title="Soon",
            deadline=(
                now + timedelta(days=1)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="Late",
            deadline=(
                now + timedelta(days=3)
            ).isoformat(),
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "sort_by": "deadline",
                "sort_order": "desc",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        titles = [
            item["title"]
            for item in response.json()["items"]
        ]

        assert titles == [
            "Late",
            "Soon",
        ]

    @pytest.mark.asyncio
    async def test_sort_by_priority(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        await create_task(
            client,
            token,
            title="Low",
            priority="Low",
            deadline=deadline,
        )

        await create_task(
            client,
            token,
            title="High",
            priority="High",
            deadline=deadline,
        )

        await create_task(
            client,
            token,
            title="Medium",
            priority="Medium",
            deadline=deadline,
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "sort_by": "priority",
                "sort_order": "asc",
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
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
    async def test_pagination(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        deadline = (
            datetime.now(timezone.utc)
            + timedelta(days=2)
        ).isoformat()

        for index in range(5):
            await create_task(
                client,
                token,
                title=f"Task {index}",
                deadline=deadline,
            )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "page": 2,
                "page_size": 2,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 5
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert data["pages"] == 3
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_combined_filters_sorting_and_pagination(
        self,
        client,
        test_user,
    ):
        token = await get_token(
            client,
            test_user,
        )

        now = datetime.now(timezone.utc)

        await create_task(
            client,
            token,
            title="Python High Later",
            description="FastAPI backend",
            priority="High",
            deadline=(
                now + timedelta(days=4)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="Python High Soon",
            description="FastAPI authentication",
            priority="High",
            deadline=(
                now + timedelta(days=1)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="Python Medium",
            description="FastAPI database",
            priority="Medium",
            deadline=(
                now + timedelta(days=2)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="Python Low",
            description="FastAPI frontend",
            priority="Low",
            deadline=(
                now + timedelta(days=1)
            ).isoformat(),
        )

        await create_task(
            client,
            token,
            title="Django High",
            description="Django backend",
            priority="High",
            deadline=(
                now + timedelta(days=1)
            ).isoformat(),
        )

        response = await client.get(
            "/api/v1/tasks",
            params={
                "search": "Python",
                "priority": "High",
                "deadline_from": (
                    now + timedelta(hours=12)
                ).isoformat(),
                "deadline_to": (
                    now + timedelta(days=3)
                ).isoformat(),
                "sort_by": "deadline",
                "sort_order": "asc",
                "page": 1,
                "page_size": 1,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] == 1
        assert data["page"] == 1
        assert data["page_size"] == 1
        assert data["pages"] == 1

        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == (
            "Python High Soon"
        )