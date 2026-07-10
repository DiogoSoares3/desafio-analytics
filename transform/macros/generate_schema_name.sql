{#-
  Use a custom schema name literally (not prefixed with the target schema).
  Lets seeds land in a dedicated `adventure_works` (Bronze) schema so the raw
  source can be declared over them, while models without a custom schema stay
  in the target schema. See ADR-0009.
-#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
