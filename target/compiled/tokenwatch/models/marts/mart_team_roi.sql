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
        10 * (SUM(output_tokens) / NULLIF(SUM(total_tokens), 0))
        * (1 - (SUM(cost_usd) / NULLIF(MAX(SUM(cost_usd)) OVER (), 0)))
        + 1
    , 1)                            AS roi_score
FROM base
GROUP BY 1, 2
ORDER BY 1, 2