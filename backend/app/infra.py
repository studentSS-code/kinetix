import json
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any


class MemoryCache:
    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        return self._values.get(key)

    async def set(self, key: str, value: Any, expire: int | timedelta = 300) -> None:
        self._values[key] = value

    async def close(self) -> None:
        return None


async def create_cache(redis_url: str) -> tuple[Any, str]:
    try:
        from redis.asyncio import Redis
        client = Redis.from_url(redis_url, decode_responses=True)
        await client.ping()
        return client, "redis"
    except Exception:
        return MemoryCache(), "memory"


async def cached(cache: Any, key: str, loader: Callable[[], Awaitable[Any]], ttl: int = 300) -> Any:
    value = await cache.get(key)
    if value is not None:
        return json.loads(value) if isinstance(value, str) else value
    value = await loader()
    encoded = json.dumps(value, default=str)
    await cache.set(key, encoded, ex=ttl) if not isinstance(cache, MemoryCache) else await cache.set(key, value, ttl)
    return value


class Database:
    def __init__(self, url: str) -> None:
        self.url = url
        self.pool: Any = None
        self.mode = "memory"

    async def connect(self) -> None:
        try:
            import asyncpg
            self.pool = await asyncpg.create_pool(self.url, min_size=1, max_size=5)
            self.mode = "postgres"
            async with self.pool.acquire() as connection:
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS trips (
                        id UUID PRIMARY KEY,
                        destination TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS profiles (
                        id UUID PRIMARY KEY,
                        display_name TEXT NOT NULL,
                        preferences JSONB NOT NULL DEFAULT '{}'
                    );
                    CREATE TABLE IF NOT EXISTS transactions (
                        id UUID PRIMARY KEY,
                        trip_id UUID NOT NULL,
                        description TEXT NOT NULL,
                        amount_eur NUMERIC NOT NULL,
                        participants JSONB NOT NULL DEFAULT '[]',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
        except Exception:
            self.pool = None

    async def save_trip(self, trip_id: str, destination: str, payload: dict[str, Any]) -> None:
        if self.pool:
            await self.pool.execute("INSERT INTO trips (id, destination, payload) VALUES ($1, $2, $3)", trip_id, destination, json.dumps(payload, default=str))

    async def save_transaction(self, transaction_id: str, payload: dict[str, Any]) -> None:
        if self.pool:
            await self.pool.execute("INSERT INTO transactions (id, trip_id, description, amount_eur, participants) VALUES ($1, $2, $3, $4, $5)", transaction_id, payload["trip_id"], payload["description"], payload["amount_eur"], json.dumps(payload["participants"]))

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
