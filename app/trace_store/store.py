import json
import structlog
from datetime import datetime
from typing import Any, Dict
import asyncpg
from app.core.config import settings

logger = structlog.get_logger()

class TraceStore:
    def __init__(self):
        self.dsn = (
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def log_trace(self, trace_id: str, trace_data: Dict[str, Any]):
        """
        Logs a decision trace to Postgres JSONB.
        Immutable log pattern.
        """
        await self.connect()
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO decision_trace (id, trace_data, created_at)
                VALUES ($1, $2, $3)
                """,
                trace_id,
                json.dumps(trace_data),
                datetime.utcnow()
            )
        logger.info("trace_logged", trace_id=trace_id)

trace_store = TraceStore()
