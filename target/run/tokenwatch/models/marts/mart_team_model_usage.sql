
  
    

create or replace transient table TOKENWATCH.RAW.mart_team_model_usage
    
    
    
    as (WITH base AS (
    SELECT * FROM TOKENWATCH.RAW.stg_token_usage
)

SELECT
    team,
    model,
    provider,
    COUNT(*)                    AS total_calls,
    ROUND(SUM(cost_usd), 2)     AS total_cost_usd,
    SUM(total_tokens)           AS total_tokens
FROM base
GROUP BY 1, 2, 3
ORDER BY 1, 4 DESC
    )
;


  