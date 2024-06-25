model = stratify(
    template_model=model,
    key= "{{ key }}",
    strata={{ strata }},
    structure= {{ structure|default(None) }},
    directed={{ directed|default(False) }},
    cartesian_control={{ cartesian_control|default(False) }},
    modify_names={{ modify_names|default(True) }},
    concepts_to_stratify={{ concepts_to_stratify|default(None) }}, #If none given, will stratify all concepts.
	params_to_stratify= {{ params_to_stratify|default(None) }} #If none given, will stratify all parameters.
)