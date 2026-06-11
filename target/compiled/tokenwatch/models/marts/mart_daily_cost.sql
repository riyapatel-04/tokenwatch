WITH base AS (
    SELECT * FROM TOKENWATCH.RAW.stg_token_usage
)

SELECT
    event_date,
    provider,
    model,
    COUNT(*)            AS total_calls,
    SUM(total_tokens)   AS total_tokens,
    ROUND(SUM(cost_usd), 4) AS total_cost_usd
FROM base
GROUP BY 1, 2, 3
ORDER BY 1