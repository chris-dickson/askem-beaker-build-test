def get_params(model_config):
    params = ""
    for kk, vv in model_config.parameters.items():
        if vv.display_name:
            display_name = f" ({vv.display_name})"
        else:
            display_name = ""
        if vv.units:
            units = f" ({vv.units})"
        else:
            units = ""
        params += f"{kk}{display_name}: {vv.value}{units}\n"
    return params

print(get_params({{ var_name|default("model_config") }}))