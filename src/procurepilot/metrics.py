from prometheus_client import Counter, Histogram

ASSESSMENTS = Counter(
    "procurepilot_assessments_total",
    "Number of completed procurement assessments",
    labelnames=("risk", "status", "model_mode"),
)

REVIEWS = Counter(
    "procurepilot_reviews_total",
    "Number of human review decisions",
    labelnames=("decision",),
)

AGENT_DURATION = Histogram(
    "procurepilot_agent_duration_seconds",
    "Execution time per bounded agent",
    labelnames=("agent",),
)
