CREATE TABLE IF NOT EXISTS decision_trace (
    id UUID PRIMARY KEY,
    trace_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    policy_version TEXT
);

CREATE INDEX idx_decision_trace_created_at ON decision_trace(created_at);

CREATE TABLE IF NOT EXISTS evaluation_outcome (
    trace_id UUID PRIMARY KEY REFERENCES decision_trace(id),
    outcome_data JSONB NOT NULL,
    corrected_decision TEXT,
    is_correct BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
