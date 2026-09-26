{% test funnel_monotonicity(model, stage_columns) %}

-- Business-rule contract: funnel stage counts must be non-increasing
-- left-to-right at every grain row. A violation means a stage definition
-- regressed (e.g. someone counted visits no longer tied to a lead cohort).
select *
from {{ model }}
where false
{% for i in range(stage_columns | length - 1) %}
   or {{ stage_columns[i] }} < {{ stage_columns[i + 1] }}
{% endfor %}

{% endtest %}
