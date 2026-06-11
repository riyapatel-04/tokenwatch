WITH base AS (
    SELECT * FROM {{ ref('stg_token_usage') }}
)

SELECT
    event_week,
    provider,
    model,
    COUNT(*)                    AS total_calls,
    SUM(total_tokens)           AS total_tokens,
    ROUND(SUM(cost_usd), 4)     AS total_cost_usd,
    ROUND(AVG(cost_usd), 6)     AS avg_cost_per_call
FROM base
GROUP BY 1, 2, 3
ORDER BY 1, 3