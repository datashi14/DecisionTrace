import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.trace_store.store import trace_store

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture(autouse=True)
async def mock_db(mocker):
    # Mock trace_store methods to avoid needing a live DB for these tests
    mocker.patch("app.trace_store.store.trace_store.connect", return_value=None)
    mocker.patch("app.trace_store.store.trace_store.disconnect", return_value=None)
    mocker.patch("app.trace_store.store.trace_store.log_trace", return_value=None)
    yield

