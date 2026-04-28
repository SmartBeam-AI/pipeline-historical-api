"""Database connection pool for TimescaleDB (read-only)."""

import os
import ssl
import asyncpg
from urllib.parse import quote_plus
from contextlib import asynccontextmanager


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self, min_size=2, max_size=10):
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            user = os.getenv("DB_USER")
            password = quote_plus(os.getenv("DB_PASSWORD", ""))
            host = os.getenv("DB_HOST")
            port = os.getenv("DB_PORT", "5432")
            name = os.getenv("DB_NAME")
            dsn = f"postgresql://{user}:{password}@{host}:{port}/{name}"

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        self.pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=min_size,
            max_size=max_size,
            ssl=ssl_ctx,
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