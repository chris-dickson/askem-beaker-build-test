import copy, requests
amr_json = requests.get("{{ model_url }}", headers={{auth_header}}).json()
{{ var_name|default("model") }} = model_from_json(amr_json)
_model_orig = copy.deepcopy({{ var_name|default("model") }})