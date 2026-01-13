# DecisionTrace

A safety-first Applied AI decision system that knows when not to act.

---

## Why I Built This

Over the last few years, the most consistent failure mode I’ve observed in applied AI systems is not lack of capability, but **misplaced confidence.**

As models have become more powerful, it has become easier to produce convincing outputs and increasingly autonomous workflows. What has not kept pace is our ability to bound those decisions, inspect why they were made, and refuse to act when the situation exceeds what the system can safely justify.

**DecisionTrace** explores a different design philosophy. Instead of asking _“How do we make the system act more often?”_, this project asks: _“Under what conditions should the system not act at all?”_

Safety is treated as a property of the full decision pipeline, not of the model alone. Hard constraints run before any model call. Cheaper shadow models can veto more capable ones. Cost is treated as a risk signal. Every decision is traceable, auditable, and evaluable after the fact.

---

## Technical Features: The Safety Stack

### 1. Deterministic Shadow Policies (Hard Constraints)

Logic-based guardrails that run before any LLM calls. If a transaction violates a hard invariant (e.g., $10k+ from an unverified user), the system returns **ABSTAIN** immediately. This guarantees safety and eliminates unnecessary inference cost.
_See: `app/core/hard_constraints.py`_

### 2. Asymmetric Safety Shadow (Second-Model Override)

Every **ACT** decision is subject to a unilateral veto by a smaller, cheaper Safety Shadow model (Claude 3.5 Haiku). If the shadow model flags a risk that the primary model (Sonnet) missed, the action is automatically downgraded to **ABSTAIN**. Safety is not a democracy; it is a system of overrides.
_See: `app/decision_engine/engine.py`_

### 3. Cost-Aware Risk Gates (VoI)

Implements **Value of Information (VoI)** assessment. If the estimated LLM cost for a decision exceeds a safety threshold (relative to transaction value), the system refuses to act. **Cost is treated as a proxy for epistemic uncertainty and downstream blast radius.**
_See: `app/evidence_planner/planner.py`_

### 4. Semantic Trace Search

Search historical decision traces by "Reasoning Type" (e.g., _"Find every time we abstained because of Policy Ambiguity"_). This supports regulatory audits, incident post-mortems, and policy drift analysis without replaying production traffic.
_See: `app/trace_store/search.py`_

### 5. Calibration Loop (Evaluation Engine)

A post-hoc engine that compares system decisions against real-world outcomes to calculate:

- **False ACT Rate**: Frequency of dangerous incorrect actions.
- **Overconfidence Penalty**: Disproportionate penalty for high-confidence incorrect decisions.
- **Confidence Calibration**: Relationship between model confidence and actual accuracy.
  _See: `app/evaluation/calibration.py`_

---

## Safety Guarantees & System Invariants

### Invariant 1: Fail-Closed by Default

If any of the following occur, the system must return **ABSTAIN**:

- Model timeout or malformed response
- Policy load failure
- Trace persistence failure
- Confidence below policy threshold
- Missing required evidence

### Invariant 2: No Untraced Actions

An **ACT** decision cannot occur unless a decision trace has been successfully written (append-only), policy version recorded, and cost/latency measured. **If trace persistence fails, the decision is revoked.**

### Invariant 3: Confidence Is Not Authority

Model confidence is advisory, not determinative. Hard constraints, safety shadows, and policy gates may override high-confidence outputs without appeal.

---

## API Contracts

### 1. Decisions API (`POST /api/v1/decide`)

The core endpoint for submitting decision requests.

**Request Structure:**

```json
{
  "context": { "user_id": "user_123", "is_verified": true, "region": "US" },
  "signals": { "action_type": "fund_transfer", "amount": 5000 },
  "policy_id": "default"
}
```

**Response Structure (Guaranteed):**

```json
{
  "decision": "ACT | ASK | ABSTAIN",
  "confidence": 0.85,
  "risk_factors": ["large_transfer"],
  "missing_information": [],
  "failure_modes": [],
  "cost_estimate": { "tokens": 1240, "latency_ms": 1150 },
  "rationale": "High-confidence transfer for verified user...",
  "trace_id": "uuid-v4"
}
```

### 2. Evaluations API (`GET /api/v1/calibration`)

Triggers a calibration report based on historical traces and their ground truth outcomes.

**Response Metrics:** `false_act_rate`, `calibration_score`, `overconfidence_penalty_total`, `conservative_abstain_count`.

---

## Assets & Governance

### Incident Management

We provide a standardized **Post-Mortem Template** for senior risk reviews.
_See: `docs/post_mortems/template.md`_

### Walkthrough Cases

See reality-grounded scenarios like **The $50k Shadow Veto Case** to understand system behavior in high-stakes environments.
_See: `docs/walkthroughs/scenario_shadow_veto.md`_

---

## What This System Refuses to Do

DecisionTrace intentionally does **not**:

- Self-modify policies or learn online from single outcomes.
- Perform autonomous retries after abstention.
- Escalate confidence to force action.
- Optimise for decision throughput over safety.

---

## Quick Start

1. **Setup**: `pip install fastapi uvicorn structlog asyncpg anthropic redis PyYAML jinja2 requests`
2. **Environment**: `cp .env.example .env` (Add `ANTHROPIC_API_KEY`)
3. **Infrastructure**: `docker compose up -d`
4. **Run**: `uvicorn app.main:app --reload`
5. **Test**: `python tests/manual_test.py`
