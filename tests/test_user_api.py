import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.models.user import User

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
async def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

class TestUserAPI:
    
    def test_create_user_success(self, client):
        """Test successful user creation"""
        user_data = {
            "telegram_id": "123456789",
            "name": "Test User",
            "gender": "male",
            "age": 25
        }
        
        response = client.post("/users/", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == user_data["telegram_id"]
        assert data["name"] == user_data["name"]
        assert data["gender"] == user_data["gender"]
        assert data["age"] == user_data["age"]
        assert "id" in data
    
    def test_create_user_duplicate_telegram_id(self, client):
        """Test creating user with duplicate telegram_id"""
        user_data = {
            "telegram_id": "123456789",
            "name": "Test User",
            "gender": "male",
            "age": 25
        }
        
        # Create first user
        response1 = client.post("/users/", json=user_data)
        assert response1.status_code == 200
        
        # Try to create second user with same telegram_id
        response2 = client.post("/users/", json=user_data)
        assert response2.status_code == 400
        assert "User already exists" in response2.json()["detail"]
    
    def test_get_user_by_telegram_id_success(self, client):
        """Test getting user by telegram_id"""
        # Create user first
        user_data = {
            "telegram_id": "123456789",
            "name": "Test User",
            "gender": "male",
            "age": 25
        }
        create_response = client.post("/users/", json=user_data)
        assert create_response.status_code == 200
        
        # Get user by telegram_id
        response = client.get("/users/123456789")
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == user_data["telegram_id"]
    
    def test_get_user_by_telegram_id_not_found(self, client):
        """Test getting non-existent user by telegram_id"""
        response = client.get("/users/nonexistent")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_get_user_by_id_success(self, client):
        """Test getting user by ID"""
        # Create user first
        user_data = {
            "telegram_id": "123456789",
            "name": "Test User",
            "gender": "male",
            "age": 25
        }
        create_response = client.post("/users/", json=user_data)
        assert create_response.status_code == 200
        created_user = create_response.json()
        
        # Get user by ID
        response = client.get(f"/users/by-id/{created_user['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_user["id"]
    
    def test_get_user_by_id_not_found(self, client):
        """Test getting non-existent user by ID"""
        response = client.get("/users/by-id/999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_get_all_users(self, client):
        """Test getting all users"""
        # Create multiple users
        users_data = [
            {"telegram_id": "111", "name": "User 1", "gender": "male", "age": 25},
            {"telegram_id": "222", "name": "User 2", "gender": "female", "age": 30},
            {"telegram_id": "333", "name": "User 3", "gender": "male", "age": 35}
        ]
        
        for user_data in users_data:
            response = client.post("/users/", json=user_data)
            assert response.status_code == 200
        
        # Get all users
        response = client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_update_user_success(self, client):
        """Test successful user update"""
        # Create user first
        user_data = {
            "telegram_id": "123456789",
            "name": "Test User",
            "gender": "male",
            "age": 25
        }
        create_response = client.post("/users/", json=user_data)
        assert create_response.status_code == 200
        created_user = create_response.json()
        
        # Update user
        update_data = {
            "telegram_id": "987654321",
            "name": "Updated User",
            "gender": "female",
            "age": 30
        }
        
        response = client.put(f"/users/{created_user['id']}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == update_data["telegram_id"]
        assert data["name"] == update_data["name"]
        assert data["gender"] == update_data["gender"]
        assert data["age"] == update_data["age"]
    
    def test_update_user_not_found(self, client):
        """Test updating non-existent user"""
        update_data = {
            "telegram_id": "987654321",
            "name": "Updated User",
            "gender": "female",
            "age": 30
        }
        
        response = client.put("/users/999", json=update_data)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"] 