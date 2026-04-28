"""API routes for pump lifecycle testbed — 3 endpoints only."""

import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Query

from app.database import db
from app.config import FQN

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check API and database connectivity."""
    db_ok = False
    try:
        async with db.connection() as conn:
            await conn.fetchval("SELECT 1")
            db_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok else "error",
        "db_connected": db_ok,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/latest")
async def latest_readings(
    pump_id: Optional[str] = Query(None, description="Filter by pump ID"),
    testbed: Optional[int] = Query(None, description="Filter by testbed"),
    limit: int = Query(100, ge=1, le=10000, description="Number of rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip for pagination"),
):
    """Get the most recent readings, ordered by time descending (UTC)."""
    clauses = []
    params = []
    idx = 1

    if pump_id:
        clauses.append(f"pump_id = ${idx}")
        params.append(pump_id)
        idx += 1
    if testbed is not None:
        clauses.append(f"testbed = ${idx}")
        params.append(testbed)
        idx += 1

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM {FQN} {where} ORDER BY time DESC LIMIT {limit} OFFSET {offset}"

    t0 = time.perf_counter()
    async with db.connection() as conn:
        rows = await conn.fetch(sql, *params)
    elapsed = (time.perf_counter() - t0) * 1000

    columns = [str(k) for k in rows[0].keys()] if rows else []
    return {
        "columns": columns,
        "rows": [dict(r) for r in rows],
        "row_count": len(rows),
        "query_time_ms": round(elapsed, 2),
    }


@router.get("/test-data")
async def test_data(
    pump_id: str = Query(..., description="Pump ID (required)"),
    start: Optional[datetime] = Query(None, description="Test start time in UTC"),
    end: Optional[datetime] = Query(None, description="Test end time in UTC"),
    testbed: Optional[int] = Query(None, description="Filter by testbed"),
    limit: int = Query(10000, ge=1, le=100000, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip for pagination"),
):
    """Get all data for a pump's test run between start and end time (oldest first)."""
    if start and end and end < start:
        return {"error": "end must not be before start"}

    clauses = ["pump_id = $1"]
    params: list = [pump_id]
    idx = 2

    if start:
        clauses.append(f"time >= ${idx}")
        params.append(start)
        idx += 1
    if end:
        clauses.append(f"time <= ${idx}")
        params.append(end)
        idx += 1
    if testbed is not None:
        clauses.append(f"testbed = ${idx}")
        params.append(testbed)
        idx += 1

    where = "WHERE " + " AND ".join(clauses)
    sql = f"SELECT * FROM {FQN} {where} ORDER BY time ASC LIMIT {limit} OFFSET {offset}"

    t0 = time.perf_counter()
    async with db.connection() as conn:
        rows = await conn.fetch(sql, *params)
    elapsed = (time.perf_counter() - t0) * 1000

    columns = [str(k) for k in rows[0].keys()] if rows else []
    return {
        "columns": columns,
        "rows": [dict(r) for r in rows],
        "row_count": len(rows),
        "query_time_ms": round(elapsed, 2),
    }