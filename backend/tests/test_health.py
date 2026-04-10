import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "5.1.0"


@pytest.mark.anyio
async def test_health_does_not_require_auth(client: AsyncClient) -> None:
    """Health endpoint must be accessible without any token."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_v1_prefix_404_on_unknown_route(client: AsyncClient) -> None:
    """Unknown v1 routes must 404, not 500."""
    response = await client.get("/v1/does-not-exist")
    assert response.status_code == 404
