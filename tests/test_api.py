import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database.db import Base, get_db


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Override database dependency for testing"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def setup_database():
    """Setup test database"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(setup_database):
    """Create test client"""
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CaissaAnalytics"
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_analyze_endpoint_validation(client):
    """Test PGN analysis endpoint validation"""
    # Test with empty list
    response = await client.post("/api/analyze", json={"pgns": []})
    assert response.status_code == 422
    
    # Test with too many PGNs
    response = await client.post("/api/analyze", json={"pgns": ["test"] * 101})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_endpoint_success(client):
    """Test PGN analysis endpoint with valid data"""
    test_pgn = """[Event "Test Game"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 1-0"""
    
    response = await client.post("/api/analyze", json={"pgns": [test_pgn]})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["games_count"] == 1
    assert len(data["game_ids"]) == 1


@pytest.mark.asyncio
async def test_get_game_not_found(client):
    """Test getting non-existent game"""
    response = await client.get("/api/games/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_game_status_not_found(client):
    """Test getting status of non-existent game"""
    response = await client.get("/api/games/999/status")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_games_empty(client):
    """Test listing games when none exist"""
    response = await client.get("/api/games")
    assert response.status_code == 200
    assert response.json() == []
