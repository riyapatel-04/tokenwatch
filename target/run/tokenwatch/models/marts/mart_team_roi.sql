
  create or replace   view TOKENWATCH.RAW.mart_team_roi
  
  
  
  
  as (
    WITH base AS (
    SELECT * FROM TOKENWATCH.RAW.stg_token_usage
)

SELECT
    event_week,
    team,
    COUNT(*)                        AS total_calls,
    SUM(total_tokens)               AS total_tokens,
    ROUND(SUM(cost_usd), 4)         AS total_cost_usd,
    ROUND(AVG(output_tokens * 1.0 / NULLIF(input_tokens, 0)), 4) AS output_ratio,
    ROUND(
        (AVG(output_tokens * 1.0 / NULLIF(input_tokens, 0)) * 10)
        / NULLIF(SUM(cost_usd), 0) * 100, 2
    )                               AS roi_score
FROM base
GROUP BY 1, 2
ORDER BY 1, 2
  );

