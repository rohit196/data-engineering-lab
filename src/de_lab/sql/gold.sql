CREATE OR REPLACE TABLE gold.daily_metrics AS
SELECT
    CAST(occurred_at AS DATE) AS event_date_utc,
    category,
    count(*) AS event_count,
    count(DISTINCT entity_id) AS unique_entities,
    sum(amount_cents) AS total_amount_cents
FROM silver.events
GROUP BY event_date_utc, category;
