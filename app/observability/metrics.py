from prometheus_client import Counter, Histogram

# Decision Metrics
decisions_total = Counter(
    "decisiontrace_decisions_total",
    "Total decisions made",
    ["decision_outcome", "policy_id"]
)

decision_latency_seconds = Histogram(
    "decisiontrace_decision_latency_seconds",
    "End-to-end decision latency",
    ["policy_id"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Safety Metrics
shadow_vetoes_total = Counter(
    "decisiontrace_shadow_vetoes_total",
    "Count of primary ACT decisions vetoed by the safety shadow",
    ["policy_id"]
)

hard_constraint_violations_total = Counter(
    "decisiontrace_hard_violations_total",
    "Count of deterministic hard constraint violations",
    ["policy_id"]
)

# Cost Metrics
tokens_consumed_total = Counter(
    "decisiontrace_tokens_total",
    "Total LLM tokens consumed",
    ["model", "type"] # type: input/output
)

llm_latency_seconds = Histogram(
    "decisiontrace_llm_latency_seconds",
    "Latency of individual LLM calls",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)
