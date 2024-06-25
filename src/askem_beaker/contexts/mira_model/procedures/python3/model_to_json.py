if "{{ schema_name }}" == "petrinet":
    from mira.modeling.amr.petrinet import template_model_to_petrinet_json
    template_model_to_petrinet_json({{ var_name|default("model") }})

if "{{ schema_name }}" == "regnet":
    from mira.modeling.amr.regnet import template_model_to_regnet_json
    template_model_to_regnet_json({{ var_name|default("model") }})

if "{{ schema_name }}" == "stockflow":
    from mira.modeling.amr.stockflow import template_model_to_stockflow_json
    template_model_to_stockflow_json({{ var_name|default("model") }})