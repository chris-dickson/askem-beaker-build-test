{% for var_name, definition in variables.items() %}
{{ var_name }} = parse_json_acset(SummationDecapode{Symbol, Symbol, Symbol},"""{{ definition }}""")
_model_reset_cache[:{{ var_name }}] = {{ var_name }}
{% endfor %}
