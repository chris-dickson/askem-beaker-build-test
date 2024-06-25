parameter_values = {{ parameter_values['parameter_values'] }}
for kk, vv in parameter_values.items():
    {{ var_name|default("model_config") }}.parameters[kk].value = vv