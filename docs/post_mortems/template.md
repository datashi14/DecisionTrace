# Incident Post-Mortem: [Incident ID]

**Date:** [YYYY-MM-DD]  
**Severity:** [Critical | High | Medium]  
**Status:** [Resolved | Investigating]  
**Trace ID:** `[UUID]`

---

## Executive Summary

[Brief description of what went wrong, the system's decision, and the real-world impact.]

## The Decision Trace

- **System Decision:** `ACT | ASK | ABSTAIN`
- **System Confidence:** `0.XX`
- **Policy Version:** `vX.Y.Z`
- **Primary Model:** `claude-3-5-sonnet`
- **Shadow Model:** `claude-3-5-haiku`

## Root Cause Analysis

### 1. The Trigger

[What input signals caused the unexpected behavior?]

### 2. Why the System Failed (or Succeeded in Restraint)

- **Primary Model Reasoning:** [Quote from rationale]
- **Shadow Veto Status:** [Triggered / Not Triggered]
- **Hard Constraints:** [Bypassed / Not Applicable]

### 3. Evaluation Gap

[Was this failure mode identified in the Evidence Planner? Why/why not?]

## Corrective Actions

- [ ] Policy Update: [Link to PR]
- [ ] New Hard Constraint: [Rule name]
- [ ] Calibration adjustment: [Target metric]

---

## Lessons Learned

[What does this tell us about the current bounds of our safety shadow?]
