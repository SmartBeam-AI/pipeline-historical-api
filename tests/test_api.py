"""Tests for pump lifecycle API endpoints."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_pump_row():
    return {
        "time": datetime(2025, 6, 1, 10, 0, 0),
        "owner": "acme_corp",
        "gateway_id": "GW-001",
        "pump_id": "PUMP-001",
        "testbed": "TB-01",
        "rpm": 1450.5,
        "suction_pressure": 2.3,
        "discharge_pressure": 8.7,
        "pump_velocity_x": 0.12, "pump_velocity_y": 0.08, "pump_velocity_z": 0.15,
        "pump_acceleration_x": 1.2, "pump_acceleration_y": 0.9, "pump_acceleration_z": 1.5,
        "pump_acoustic_db": 72.3,
        "pump_temperature": 45.2,
        "motor_velocity_x": 0.10, "motor_velocity_y": 0.07, "motor_velocity_z": 0.11,
        "motor_acceleration_x": 1.0, "motor_acceleration_y": 0.8, "motor_acceleration_z": 1.1,
        "motor_acoustic_db": 68.1,
        "motor_temperature": 52.4,
        "power_voltage_r": 415.2, "power_voltage_y": 413.8, "power_voltage_b": 416.1,
        "power_current_r": 12.5, "power_current_y": 12.3, "power_current_b": 12.6,
        "pump_type": "reciprocating",
        "label": "normal",
        "flow_rate": 150.0,
        "fluid_temperature": 28.5,
    }


def mock_connection(fetch_result=None, fetchrow_result=None, fetchval_result=None):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=fetch_result or [])
    conn.fetchrow = AsyncMock(return_value=fetchrow_result)
    conn.fetchval = AsyncMock(return_value=fetchval_result or 1)

    class MockCtx:
        async def __aenter__(self):
            return conn
        async def __aexit__(self, *args):
            pass

    db.connection = MockCtx
    return conn


@pytest.mark.asyncio
async def test_health_ok():
    mock_connection(fetchval_result=1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db_connected"] is True


@pytest.mark.asyncio
async def test_health_db_down():
    conn = AsyncMock()
    conn.fetchval = AsyncMock(side_effect=Exception("connection refused"))
    class MockCtx:
        async def __aenter__(self):
            return conn
        async def __aexit__(self, *args):
            pass
    db.connection = MockCtx
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_list_pumps():
    mock_connection(fetch_result=[{
        "pump_id": "PUMP-001", "pump_type": "reciprocating",
        "testbed": "TB-01", "owner": "acme",
        "last_seen": datetime(2025, 6, 1), "record_count": 50000,
    }])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["pump_id"] == "PUMP-001"


@pytest.mark.asyncio
async def test_list_pumps_with_filter():
    mock_connection(fetch_result=[])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps?testbed=TB-01&owner=acme")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_testbeds():
    mock_connection(fetch_result=[
        {"testbed": "TB-01", "pump_count": 3, "last_activity": datetime(2025, 6, 1)},
        {"testbed": "TB-02", "pump_count": 1, "last_activity": datetime(2025, 5, 30)},
    ])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/testbeds")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_metrics():
    mock_connection()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/metrics")
    assert resp.status_code == 200
    assert "rpm" in resp.json()
    assert "pump_temperature" in resp.json()


@pytest.mark.asyncio
async def test_pump_summary():
    summary_row = {
        "pump_id": "PUMP-001", "testbed": "TB-01", "pump_type": "reciprocating",
        "last_reading": datetime(2025, 6, 1, 10, 0, 0),
        "rpm": 1450.5, "suction_pressure": 2.3, "discharge_pressure": 8.7,
        "flow_rate": 150.0, "pump_temperature": 45.2, "motor_temperature": 52.4,
        "fluid_temperature": 28.5, "pump_acoustic_db": 72.3, "motor_acoustic_db": 68.1,
        "power_voltage_r": 415.2, "power_voltage_y": 413.8, "power_voltage_b": 416.1,
        "power_current_r": 12.5, "power_current_y": 12.3, "power_current_b": 12.6,
    }
    mock_connection(fetchrow_result=summary_row)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/summary")
    assert resp.status_code == 200
    assert resp.json()["rpm"] == 1450.5


@pytest.mark.asyncio
async def test_pump_summary_not_found():
    mock_connection(fetchrow_result=None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/NONEXISTENT/summary")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_pump_raw_data(sample_pump_row):
    mock_connection(fetch_result=[sample_pump_row])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/data?limit=10")
    assert resp.status_code == 200
    assert resp.json()["row_count"] == 1


@pytest.mark.asyncio
async def test_pump_raw_data_with_time_range(sample_pump_row):
    mock_connection(fetch_result=[sample_pump_row])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/data?start=2025-06-01T00:00:00&end=2025-06-01T23:59:59&limit=50")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_vibration_endpoint():
    vib_row = {
        "time": datetime(2025, 6, 1, 10, 0, 0),
        "pump_velocity_x": 0.12, "pump_velocity_y": 0.08, "pump_velocity_z": 0.15,
        "pump_acceleration_x": 1.2, "pump_acceleration_y": 0.9, "pump_acceleration_z": 1.5,
        "motor_velocity_x": 0.10, "motor_velocity_y": 0.07, "motor_velocity_z": 0.11,
        "motor_acceleration_x": 1.0, "motor_acceleration_y": 0.8, "motor_acceleration_z": 1.1,
    }
    mock_connection(fetch_result=[vib_row])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/vibration?limit=100")
    assert resp.status_code == 200
    assert resp.json()[0]["pump_velocity_x"] == 0.12


@pytest.mark.asyncio
async def test_power_endpoint():
    power_row = {
        "time": datetime(2025, 6, 1, 10, 0, 0),
        "power_voltage_r": 415.2, "power_voltage_y": 413.8, "power_voltage_b": 416.1,
        "power_current_r": 12.5, "power_current_y": 12.3, "power_current_b": 12.6,
    }
    mock_connection(fetch_result=[power_row])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/power")
    assert resp.status_code == 200
    assert resp.json()[0]["power_voltage_r"] == 415.2


@pytest.mark.asyncio
async def test_timeseries_valid_metric():
    bucket_rows = [
        {"bucket": datetime(2025, 6, 1, 10, 0), "value": 1450.0},
        {"bucket": datetime(2025, 6, 1, 10, 1), "value": 1455.2},
    ]
    mock_connection(fetch_result=bucket_rows)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/timeseries?metric=rpm&bucket=1+minute&agg=avg")
    assert resp.status_code == 200
    assert resp.json()["metric"] == "rpm"
    assert resp.json()["point_count"] == 2


@pytest.mark.asyncio
async def test_timeseries_invalid_metric():
    mock_connection()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/timeseries?metric=DROP_TABLE&bucket=1+minute&agg=avg")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_timeseries_invalid_agg():
    mock_connection()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/timeseries?metric=rpm&bucket=1+minute&agg=DROP")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_compare_pumps():
    rows = [
        {"pump_id": "PUMP-001", "bucket": datetime(2025, 6, 1, 10, 0), "value": 1450.0},
        {"pump_id": "PUMP-002", "bucket": datetime(2025, 6, 1, 10, 0), "value": 1380.0},
    ]
    mock_connection(fetch_result=rows)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/compare?pump_ids=PUMP-001,PUMP-002&metric=rpm&bucket=1+minute&agg=avg")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_compare_invalid_metric():
    mock_connection()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/compare?pump_ids=PUMP-001&metric=hackers&bucket=1+minute&agg=avg")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_labels():
    rows = [
        {"label": "normal", "count": 45000, "first_seen": datetime(2025, 1, 1), "last_seen": datetime(2025, 6, 1)},
        {"label": "cavitation", "count": 120, "first_seen": datetime(2025, 3, 15), "last_seen": datetime(2025, 5, 20)},
    ]
    mock_connection(fetch_result=rows)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/labels")
    assert resp.status_code == 200
    assert resp.json()["row_count"] == 2


@pytest.mark.asyncio
async def test_pagination_limits():
    mock_connection(fetch_result=[])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/pumps/PUMP-001/data?limit=99999")
        assert resp.status_code == 422
        resp = await client.get("/api/v1/pumps/PUMP-001/data?limit=0")
        assert resp.status_code == 422
        resp = await client.get("/api/v1/pumps/PUMP-001/data?limit=500")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_only_get_methods_allowed():
    mock_connection()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/pumps", content="{}")
        assert resp.status_code == 405
        resp = await client.delete("/api/v1/pumps/PUMP-001/summary")
        assert resp.status_code == 405
