import structlog
from fastapi import APIRouter, Query
from app.evaluation.calibration import calibration_loop, CalibrationMetrics

router = APIRouter()
logger = structlog.get_logger()

@router.get("/calibration", response_model=CalibrationMetrics)
async def get_calibration_report(
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Triggers a calibration analysis on historical decision traces.
    Returns metrics on False ACT rates, confidence calibration, and overconfidence penalties.
    """
    logger.info("calibration_report_requested", limit=limit)
    metrics = await calibration_loop.run_calibration(limit=limit)
    return metrics
