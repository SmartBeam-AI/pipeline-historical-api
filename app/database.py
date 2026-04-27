"""Database connection pool for TimescaleDB (read-only)."""

import asyncpg
from contextlib import asynccontextmanager
from typing import Optional


class Database:
    """Manages an asyncpg connection pool to TimescaleDB."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(
        self,
        dsn: str,
        min_size: int = 2,
        max_size: int = 10,
    ):
        self.pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
            server_settings={"default_transaction_read_only": "on"},
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def connection(self):
        async with self.pool.acquire() as conn:
            yield conn


db = Database()