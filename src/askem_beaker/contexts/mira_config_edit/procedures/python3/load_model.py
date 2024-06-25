import copy, requests
amr_json = dict({{ model }})
{{ var_name|default("model_config") }} = model_from_json(amr_json)
_model_orig = copy.deepcopy({{ var_name|default("model_config") }})
