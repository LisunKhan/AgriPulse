-- Idempotent upgrade for existing local volumes (hybrid public_id).
-- Safe to run multiple times.

ALTER TABLE telemetry
    ADD COLUMN IF NOT EXISTS public_id UUID;

UPDATE telemetry
SET public_id = gen_random_uuid()
WHERE public_id IS NULL;

ALTER TABLE telemetry
    ALTER COLUMN public_id SET DEFAULT gen_random_uuid();

DO $$
BEGIN
    ALTER TABLE telemetry ALTER COLUMN public_id SET NOT NULL;
EXCEPTION
    WHEN others THEN
        NULL;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_telemetry_public_id
    ON telemetry (public_id);

ALTER TABLE alerts
    ADD COLUMN IF NOT EXISTS public_id UUID;

UPDATE alerts
SET public_id = gen_random_uuid()
WHERE public_id IS NULL;

ALTER TABLE alerts
    ALTER COLUMN public_id SET DEFAULT gen_random_uuid();

DO $$
BEGIN
    ALTER TABLE alerts ALTER COLUMN public_id SET NOT NULL;
EXCEPTION
    WHEN others THEN
        NULL;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_public_id
    ON alerts (public_id);
