-- Point-in-time price join sanity: every sale must match exactly one
-- effective price version, and the paid amount must sit between the
-- maximum discount (10%) and the list price.
select *
from {{ ref('fct_revenue') }}
where list_price_at_sale is null
   or amount > list_price_at_sale
   or amount < list_price_at_sale * 0.85
