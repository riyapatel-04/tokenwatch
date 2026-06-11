
  create or replace   view TOKENWATCH.RAW.my_second_dbt_model
  
  
  
  
  as (
    -- Use the `ref` function to select from other models

select *
from TOKENWATCH.RAW.my_first_dbt_model
where id = 1
  );

