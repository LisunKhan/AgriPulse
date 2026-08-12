-- AgriPulse telemetry schema (Milestone 2)
-- Applied automatically on first Postgres container start.

CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    temperature_c DECIMAL(5, 2) NOT NULL,
    humidity_pct DECIMAL(5, 2) NOT NULL,
    lat DECIMAL(9, 6) NOT NULL,
    lng DECIMAL(9, 6) NOT NULL,
    status VARCHAR(50) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_id
    ON telemetry (device_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_recorded_at
    ON telemetry (recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_recorded
    ON telemetry (device_id, recorded_at DESC);

-- Threshold / spoilage alerts (used by backend in Milestone 3)
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    temperature_c DECIMAL(5, 2),
    humidity_pct DECIMAL(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_alerts_created_at
    ON alerts (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_device_id
    ON alerts (device_id);
