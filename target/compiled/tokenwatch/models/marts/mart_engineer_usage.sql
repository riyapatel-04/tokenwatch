WITH base AS (
    SELECT * FROM TOKENWATCH.RAW.stg_token_usage
)

SELECT
    engineer,
    team,
    COUNT(*)                        AS total_calls,
    SUM(total_tokens)               AS total_tokens,
    ROUND(SUM(cost_usd), 2)         AS total_cost_usd,
    ROUND(AVG(output_tokens * 1.0 / NULLIF(input_tokens, 0)), 2) AS output_ratio,
    MAX(model)                      AS top_model
FROM base
GROUP BY 1, 2
ORDER BY total_cost_usd DESC