
  create or replace   view TOKENWATCH.RAW.stg_token_usage
  
  
  
  
  as (
    WITH source AS (
    SELECT * FROM TOKENWATCH.RAW.token_usage_raw
)

SELECT
    event_id,
    event_timestamp,
    project,
    team,
    engineer,
    model,
    provider,
    task_type,
    input_tokens,
    output_tokens,
    total_tokens,
    cost_usd,
    duration_ms,
    was_successful,
    DATE_TRUNC('day', event_timestamp)  AS event_date,
    DATE_TRUNC('week', event_timestamp) AS event_week
FROM source
WHERE was_successful = TRUE
AND event_timestamp >= DATEADD(day, -90, CURRENT_DATE)
  );

