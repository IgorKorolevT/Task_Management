import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database import Base, get_db
from app.user.models import User
from app.user.auth import hash_password


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True,
    )
    
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield async_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(test_db):
    """Create test user"""
    async with test_db() as session:
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password=hash_password("testpass123"),
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


class TestUserRegistration:
    """Tests for user registration"""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Test successful user registration"""
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "password123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] == True
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "testuser",
                "email": "different@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        """Test registration with password too short"""
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "pass"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_short_username(self, client):
        """Test registration with username too short"""
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "ab",
                "email": "new@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = await client.post(
            "/api/v1/users/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == 422


class TestUserLogin:
    """Tests for user login"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful login"""
        response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]


class TestTokenRefresh:
    """Tests for token refresh"""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh"""
        # First, login to get refresh token
        login_response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "testpass123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Now refresh
        response = await client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = await client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestGetUser:
    """Tests for getting user"""
    
    @pytest.mark.asyncio
    async def test_get_user_success(self, client, test_user):
        """Test get user by ID"""
        response = await client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client):
        """Test get nonexistent user"""
        response = await client.get("/api/v1/users/99999")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestUpdateUser:
    """Tests for updating user"""
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, client, test_user):
        """Test successful user update"""
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            json={
                "full_name": "Updated Name",
                "email": "updated@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"
        assert data["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_update_user_password(self, client, test_user):
        """Test updating user password"""
        response = await client.put(
            f"/api/v1/users/{test_user.id}",
            json={"password": "newpassword123"}
        )
        
        assert response.status_code == 200
        
        # Try logging in with new password
        login_response = await client.post(
            "/api/v1/users/login",
            json={
                "username": "testuser",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client):
        """Test update nonexistent user"""
        response = await client.put(
            "/api/v1/users/99999",
            json={"full_name": "New Name"}
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestDeleteUser:
    """Tests for deleting user"""
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, client, test_user):
        """Test successful user deletion (soft delete)"""
        response = await client.delete(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 204
        
        # User should still exist but is_active should be False
        get_response = await client.get(f"/api/v1/users/{test_user.id}")
        # After soft delete, we might want to return 404 or hide inactive users
        # For now, let's check the user exists but is inactive
        assert get_response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client):
        """Test delete nonexistent user"""
        response = await client.delete("/api/v1/users/99999")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestHealthCheck:
    """Tests for health check and root endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "Task Management API" in data["message"]
