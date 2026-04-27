"""API routes for pump lifecycle testbed — 3 core endpoints."""

import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.database import db
from app.config import FQN
from app.schemas import HealthResponse, QueryResult

router = APIRouter()


# =====================================================================
#  1. HEALTH CHECK
# =====================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and database connectivity."""
    db_ok = False
    try:
        async with db.connection() as conn:
            await conn.fetchval("SELECT 1")
            db_ok = True
    except Exception:
        pass
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_connected=db_ok,
        timestamp=datetime.now(timezone.utc),
    )


# =====================================================================
#  2. LATEST READINGS — most recent data with limit/offset
# =====================================================================

@router.get("/latest", response_model=QueryResult)
async def latest_readings(
    pump_id: Optional[str] = Query(None, description="Filter by pump ID"),
    testbed: Optional[int] = Query(None, description="Filter by testbed"),
    limit: int = Query(100, ge=1, le=10000, description="Number of rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip for pagination"),
):
    """
    Get the most recent readings, ordered by time descending (UTC).
    Supports pagination via limit/offset and optional filtering.
    """
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

    sql = f"SELECT *, time AT TIME ZONE 'UTC' AS time_utc FROM {FQN} {where} ORDER BY time DESC LIMIT {limit} OFFSET {offset}"

    t0 = time.perf_counter()
    async with db.connection() as conn:
        rows = await conn.fetch(sql, *params)
    elapsed = (time.perf_counter() - t0) * 1000

    columns = [str(k) for k in rows[0].keys()] if rows else []
    return QueryResult(
        columns=columns,
        rows=[dict(r) for r in rows],
        row_count=len(rows),
        query_time_ms=round(elapsed, 2),
    )


# =====================================================================
#  3. TEST DATA — full test run from start to end (latest)
# =====================================================================

@router.get("/test-data", response_model=QueryResult)
async def test_data(
    pump_id: str = Query(..., description="Pump ID (required)"),
    start: Optional[datetime] = Query(None, description="Test start time in UTC. If omitted, returns from the first reading."),
    end: Optional[datetime] = Query(None, description="Test end time in UTC. If omitted, returns up to the latest reading."),
    testbed: Optional[int] = Query(None, description="Filter by testbed"),
    limit: int = Query(10000, ge=1, le=100000, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip for pagination"),
):
    """
    Get all data for a pump's test run between start and end time.
    All timestamps are in UTC.
    - start = when the test was started
    - end = latest data (omit to get up to the most recent reading)
    - end must not be before start
    - Returns rows ordered by time ascending (oldest first)
    """
    # Validate: end must not be before start
    if start and end and end < start:
        raise HTTPException(
            status_code=400,
            detail=f"'end' ({end.isoformat()}) must not be before 'start' ({start.isoformat()})"
        )

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

    sql = f"SELECT *, time AT TIME ZONE 'UTC' AS time_utc FROM {FQN} {where} ORDER BY time ASC LIMIT {limit} OFFSET {offset}"

    t0 = time.perf_counter()
    async with db.connection() as conn:
        rows = await conn.fetch(sql, *params)
    elapsed = (time.perf_counter() - t0) * 1000

    columns = [str(k) for k in rows[0].keys()] if rows else []
    return QueryResult(
        columns=columns,
        rows=[dict(r) for r in rows],
        row_count=len(rows),
        query_time_ms=round(elapsed, 2),
    )
