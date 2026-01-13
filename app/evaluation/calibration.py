import structlog
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.trace_store.store import trace_store

logger = structlog.get_logger()

class CalibrationMetrics(BaseModel):
    total_evaluated: int = 0
    false_act_count: int = 0  # Severe: System said ACT, but it was wrong
    conservative_abstain_count: int = 0  # Opportunity cost: System said ABSTAIN, but ACT would have been safe
    correct_decision_count: int = 0
    
    # Calibration
    avg_confidence_correct: float = 0.0
    avg_confidence_incorrect: float = 0.0
    overconfidence_penalty_total: float = 0.0  # Sum of (confidence^2) where is_correct=False
    
    @property
    def false_act_rate(self) -> float:
        return self.false_act_count / self.total_evaluated if self.total_evaluated > 0 else 0.0

    @property
    def calibration_score(self) -> float:
        # Simple ratio of confidence vs correctness
        return (self.avg_confidence_correct - self.avg_confidence_incorrect)

class CalibrationLoop:
    """
    Analyzes historical decisions vs ground truth to measure calibration and regret.
    """
    
    async def run_calibration(self, limit: int = 100) -> CalibrationMetrics:
        """
        Batch process traces that have evaluation outcomes and compute safety-first metrics.
        """
        await trace_store.connect()
        async with trace_store.pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT t.id, t.trace_data, e.outcome_data 
                FROM decision_trace t
                JOIN evaluation_outcome e ON t.id = e.trace_id
                ORDER BY e.created_at DESC
                LIMIT $1
                """,
                limit
            )
            
            metrics = CalibrationMetrics(total_evaluated=len(records))
            conf_correct = []
            conf_incorrect = []
            
            for rec in records:
                trace_data = rec['trace_data']
                outcome_data = rec['outcome_data']
                
                decision = trace_data.get('decision', {}).get('decision')
                confidence = trace_data.get('decision', {}).get('confidence', 0.0)
                is_correct = outcome_data.get('is_correct', False)
                
                if is_correct:
                    metrics.correct_decision_count += 1
                    conf_correct.append(confidence)
                else:
                    conf_incorrect.append(confidence)
                    # Overconfidence Penalty: Square the confidence to penalize "arrogant errors"
                    metrics.overconfidence_penalty_total += (confidence ** 2)
                    
                    if decision == "ACT":
                        metrics.false_act_count += 1
                
                if decision == "ABSTAIN" and outcome_data.get('ground_truth_safe', False):
                    metrics.conservative_abstain_count += 1
            
            if conf_correct:
                metrics.avg_confidence_correct = sum(conf_correct) / len(conf_correct)
            if conf_incorrect:
                metrics.avg_confidence_incorrect = sum(conf_incorrect) / len(conf_incorrect)
            
            logger.info("calibration_loop_completed", 
                        false_act_rate=metrics.false_act_rate,
                        overconfidence_penalty=metrics.overconfidence_penalty_total)
            
            return metrics

calibration_loop = CalibrationLoop()
