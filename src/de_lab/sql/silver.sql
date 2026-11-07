CREATE OR REPLACE TABLE silver.events AS
SELECT
    event_id,
    entity_id,
    CAST(occurred_at AS TIMESTAMPTZ) AS occurred_at,
    lower(category) AS category,
    CAST(amount_cents AS BIGINT) AS amount_cents
FROM bronze.events;
