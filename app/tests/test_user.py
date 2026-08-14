import pytest


class TestHealth:

    @pytest.mark.asyncio
    async def test_root(self, client):
        response = await client.get("/")

        assert response.status_code == 200

        data = response.json()

        assert data["message"] == (
            "Task Management API"
        )
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {
            "status": "ok"
        }


class TestUserRegistration:

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "password123",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["username"] == "newuser"
        assert data["email"] == (
            "newuser@example.com"
        )
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Password must never be returned.
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(
            self,
            client,
            test_user,
    ):
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "testuser",
                "email": "different@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Username already registered"
        )

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
            self,
            client,
            test_user,
    ):
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Email already registered"
        )

    @pytest.mark.asyncio
    async def test_register_short_password(
            self,
            client,
    ):
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_username(
            self,
            client,
    ):
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "ab",
                "email": "new@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(
            self,
            client,
    ):
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "password123",
            },
        )

        assert response.status_code == 422


class TestUserLogin:

    @pytest.mark.asyncio
    async def test_login_success(
            self,
            client,
            test_user,
    ):
        response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_by_email(
            self,
            client,
            test_user,
    ):
        response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "test@example.com",
                "password": "testpass123",
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_login_wrong_password(
            self,
            client,
            test_user,
    ):
        response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "Invalid username or password"
        )

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(
            self,
            client,
    ):
        response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "nonexistent",
                "password": "password123",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "Invalid username or password"
        )


class TestTokenRefresh:

    @pytest.mark.asyncio
    async def test_refresh_success(
            self,
            client,
            test_user,
    ):
        login_response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            },
        )

        refresh_token = (
            login_response.json()["refresh_token"]
        )

        response = await client.post(
            "/api/v1/users/refresh",
            json={
                "refresh_token": refresh_token
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(
            self,
            client,
    ):
        response = await client.post(
            "/api/v1/users/refresh",
            json={
                "refresh_token": "invalid_token"
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "Invalid refresh token"
        )

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(
            self,
            client,
            test_user,
    ):
        login_response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            },
        )

        access_token = (
            login_response.json()["access_token"]
        )

        response = await client.post(
            "/api/v1/users/refresh",
            json={
                "refresh_token": access_token
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"] == (
            "Invalid refresh token"
        )


class TestAuthentication:

    @pytest.mark.asyncio
    async def test_me_without_token(
            self,
            client,
    ):
        response = await client.get(
            "/api/v1/users/me"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(
            self,
            client,
    ):
        response = await client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": "Bearer invalid"
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_success(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == test_user.id
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"


class TestGetUser:

    @pytest.mark.asyncio
    async def test_get_user_success(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.get(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == test_user.id
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_other_user_forbidden(
            self,
            client,
            auth_headers,
    ):
        response = await client.get(
            "/api/v1/users/99999",
            headers=auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_without_token(
            self,
            client,
            test_user,
    ):
        response = await client.get(
            f"/api/v1/users/{test_user.id}"
        )

        assert response.status_code == 401


class TestUpdateUser:

    @pytest.mark.asyncio
    async def test_update_full_name(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "full_name": "Updated Name"
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["full_name"] == (
            "Updated Name"
        )

    @pytest.mark.asyncio
    async def test_update_email(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "email": "updated@example.com"
            },
        )

        assert response.status_code == 200

        assert response.json()["email"] == (
            "updated@example.com"
        )

    @pytest.mark.asyncio
    async def test_update_username(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "username": "updateduser"
            },
        )

        assert response.status_code == 200

        assert response.json()["username"] == (
            "updateduser"
        )

    @pytest.mark.asyncio
    async def test_update_password(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "password": "newpassword123"
            },
        )

        assert response.status_code == 200

        login_response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "newpassword123",
            },
        )

        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_duplicate_username(
            self,
            client,
            auth_headers,
            test_user,
    ):
        await client.post(
            "/api/v1/users/register",
            json={
                "username": "seconduser",
                "email": "second@example.com",
                "password": "password123",
            },
        )

        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "username": "seconduser"
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Username already registered"
        )

    @pytest.mark.asyncio
    async def test_update_duplicate_email(
            self,
            client,
            auth_headers,
            test_user,
    ):
        await client.post(
            "/api/v1/users/register",
            json={
                "username": "seconduser",
                "email": "second@example.com",
                "password": "password123",
            },
        )

        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "email": "second@example.com"
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Email already registered"
        )

    @pytest.mark.asyncio
    async def test_update_other_user_forbidden(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.put(
            "/api/v1/users/99999",
            headers=auth_headers,
            json={
                "full_name": "Hacker"
            },
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_without_token(
            self,
            client,
            test_user,
    ):
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            json={
                "full_name": "Updated"
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_short_password(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
            json={
                "password": "short"
            },
        )

        assert response.status_code == 422


class TestDeleteUser:

    @pytest.mark.asyncio
    async def test_delete_user_success(
            self,
            client,
            auth_headers,
            test_user,
    ):
        response = await client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        login_response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            },
        )

        assert login_response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_user_without_token(
            self,
            client,
            test_user,
    ):
        response = await client.delete(
            f"/api/v1/users/{test_user.id}"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_other_user_forbidden(
            self,
            client,
            auth_headers,
    ):
        response = await client.delete(
            "/api/v1/users/99999",
            headers=auth_headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_deleted_user_cannot_refresh_token(
            self,
            client,
            test_user,
            auth_headers,
    ):
        login_response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            },
        )

        refresh_token = (
            login_response.json()["refresh_token"]
        )

        delete_response = await client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=auth_headers,
        )

        assert delete_response.status_code == 204

        refresh_response = await client.post(
            "/api/v1/users/refresh",
            json={
                "refresh_token": refresh_token
            },
        )

        assert refresh_response.status_code == 401
        assert refresh_response.json()["detail"] == (
            "User not found or inactive"
        )
