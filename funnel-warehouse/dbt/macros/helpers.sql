{# Parse a date rendered in any of the three known studio formats.
   ISO 2025-03-14 | 14/03/2025 | 14-Mar-2025  #}
{% macro parse_multi_date(col) %}
    coalesce(
        try_strptime({{ col }}, '%Y-%m-%d'),
        try_strptime({{ col }}, '%d/%m/%Y'),
        try_strptime({{ col }}, '%d-%b-%Y')
    )::date
{% endmacro %}

{# Parse money that may arrive as 1250000 or "Rp 1.250.000" #}
{% macro parse_money(col) %}
    try_cast(
        replace(replace(trim({{ col }}), 'Rp ', ''), '.', '')
        as bigint
    )
{% endmacro %}

{# Normalize messy boolean tokens: Y/yes/1/TRUE -> true #}
{% macro parse_bool(col) %}
    lower(trim({{ col }})) in ('y', 'yes', '1', 'true')
{% endmacro %}

{# Deterministic surrogate key #}
{% macro surrogate_key(cols) %}
    md5(concat_ws('||', {{ cols | join(", ") }}))
{% endmacro %}
