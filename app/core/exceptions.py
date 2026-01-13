class DecisionTraceError(Exception):
    """Base exception for DecisionTrace."""
    pass

class ModelTimeoutError(DecisionTraceError):
    """Raised when the LLM provider times out."""
    pass

class PolicyLoadError(DecisionTraceError):
    """Raised when a policy cannot be loaded or is invalid."""
    pass

class TracePersistenceError(DecisionTraceError):
    """Raised when the decision trace cannot be written to immutable storage."""
    pass
