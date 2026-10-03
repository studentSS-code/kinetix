from datetime import date
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_reports_fallback_infrastructure():
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_plan_trip_runs_agent_workflow_without_external_keys():
    payload = {"destination": "Lisbon", "start_date": "2026-10-18", "end_date": "2026-10-21", "travelers": 2, "budget_eur": 720, "preferences": ["local food"], "energy_level": "low"}
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/trips/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["budget"]["daily_target_eur"] == 240.0
    assert data["itinerary"][0]["pace"] == "gentle"
    assert data["trip_id"]


@pytest.mark.asyncio
async def test_invalid_hotel_dates_are_rejected():
    payload = {"city_code": "LIS", "check_in_date": date.today().isoformat(), "check_out_date": date.today().isoformat(), "adults": 2}
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/hotels", json=payload)
    assert response.status_code == 422
