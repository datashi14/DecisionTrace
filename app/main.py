from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.config import settings
from app.api.v1.decisions import router as decisions_router
from app.api.v1.evaluations import router as evaluations_router
from app.trace_store.store import trace_store
from app.observability.metrics import decisions_total, decision_latency_seconds, hard_constraint_violations_total

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB pool
    try:
        await trace_store.connect()
        logger.info("startup_db_connected")
    except Exception as e:
        logger.error("startup_db_failed", error=str(e))
    yield
    # Shutdown: Close DB pool
    await trace_store.disconnect()
    logger.info("shutdown_db_disconnected")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Instrument FastAPI with Prometheus
Instrumentator().instrument(app).expose(app)

app.include_router(decisions_router, prefix=settings.API_V1_STR, tags=["decisions"])
app.include_router(evaluations_router, prefix=settings.API_V1_STR, tags=["evaluations"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.get("/")
async def root():
    return {"message": "Welcome to DecisionTrace"}
