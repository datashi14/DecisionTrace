# DecisionTrace

A safety-first Applied AI decision system that knows when not to act.

---

## Why I Built This

Over the last few years, the most consistent failure mode I’ve observed in applied AI systems is not lack of capability, but **misplaced confidence.**

As models have become more powerful, it has become easier to produce convincing outputs and increasingly autonomous workflows. What has not kept pace is our ability to bound those decisions, inspect why they were made, and refuse to act when the situation exceeds what the system can safely justify.

**DecisionTrace** explores a different design philosophy. Instead of asking _“How do we make the system act more often?”_, this project asks: _“Under what conditions should the system not act at all?”_

Safety is treated as a property of the full decision pipeline, not of the model alone.

---

## Technical Features: The Safety Stack

### 1. Deterministic Shadow Policies (Hard Constraints)

Logic-based guardrails that run before any LLM calls. If a transaction violates a hard invariant (e.g., $10k+ from an unverified user), the system returns **ABSTAIN** immediately.
_See: `app/core/hard_constraints.py`_

### 2. Asymmetric Safety Shadow (Second-Model Override)

Every **ACT** decision is subject to a unilateral veto by a smaller, cheaper Safety Shadow model (Claude 3.5 Haiku). Safety is not a democracy; it is a system of overrides.
_See: `app/decision_engine/engine.py`_

### 3. Cost-Aware Risk Gates (VoI)

Implements **Value of Information (VoI)** assessment. If the estimated LLM cost for a decision exceeds a safety threshold, the system refuses to act. **Cost is treated as a risk signal.**
_See: `app/evidence_planner/planner.py`_

### 4. Production Observability

Full instrumentation with **Prometheus**. Track decision rates, shadow veto rates, hard violations, and token costs (p90/p95/p99 latency ready).
_See: `app/observability/metrics.py`_

### 5. Calibration & Search

Post-hoc engine for measuring confidence calibration and semantic search for auditing historical rationales.
_See: `app/evaluation/calibration.py` and `app/trace_store/search.py`_

---

## Safety Guarantees & System Invariants

1. **Fail-Closed**: Any system error (timeout, model failure, trace failure) defaults to **ABSTAIN**.
2. **No Untraced Actions**: An **ACT** decision is automatically revoked if the immutable trace cannot be successfully persisted.
3. **Confidence Is Not Authority**: Hard constraints and safety shadows override high-confidence model outputs without appeal.

---

## API & Operations

### Endpoints

- `POST /api/v1/decide`: Core decision engine.
- `GET /api/v1/calibration`: Evaluation metrics.
- `GET /metrics`: Prometheus metrics.

### Testing

- **Integration**: `pytest tests/integration/test_decision_pipeline.py`
- **Load Testing**: `locust -f tests/load/locustfile.py`

---

## Deployment (Production)

DecisionTrace is containerized for production reliability.

```bash
# 1. Provide API Key
export ANTHROPIC_API_KEY=your_key_here

# 2. Launch Stack (API, DB, Prometheus, Grafana)
docker-compose up -d
```

- **API**: `http://localhost:8000`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3000` (User: `admin`, Pass: `admin`)

---

## assets & Governance

- **Post-Mortem Template**: `docs/post_mortems/template.md`
- **Shadow Veto Scenario**: `docs/walkthroughs/scenario_shadow_veto.md`
