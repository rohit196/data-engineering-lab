CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS ops;

CREATE OR REPLACE TABLE bronze.events (
    event_id VARCHAR,
    entity_id VARCHAR,
    occurred_at VARCHAR,
    category VARCHAR,
    amount_cents VARCHAR
);
