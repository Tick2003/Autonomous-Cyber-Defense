-- schema.sql
CREATE TABLE IF NOT EXISTS raw_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    volume INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id UUID REFERENCES raw_logs(id) ON DELETE CASCADE,
    anomaly_score FLOAT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS blockchain_proofs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES alerts(id) ON DELETE CASCADE,
    sha256_hash TEXT NOT NULL,
    transaction_id TEXT NOT NULL
);
