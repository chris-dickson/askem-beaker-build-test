concepts_name_map = model.get_concepts_name_map()
if "{{ subject_name }}" not in concepts_name_map:
    subject_concept = Concept(name = "{{ subject_name }}")
else:
    subject_concept = concepts_name_map.get("{{ subject_name }}")

if "{{ parameter_name}}" not in model.parameters: #note this is checks for paremeter's symbol
    parameter_unit = Unit(expression = sympy.Symbol("{{ parameter_units}}"))
    parameters = {
        "{{ parameter_name}}": Parameter(name = "{{ parameter_name}}", value = {{ parameter_value }}, units = parameter_unit, description = "{{ parameter_description}}")
    }
else: 
    parameters = {"{{ parameter_name}}": model.parameters.get("{{ parameter_name}}")}

initials = { 
    "{{subject_name }}": Initial(concept = subject_concept, expression = sympy.Float({{subject_initial_value }}))
}

model = model.add_template(
    template = NaturalDegradation(
        subject = subject_concept,
        rate_law = safe_parse_expr("{{ template_expression }}", local_dict=_clash),
        name = "{{ template_name }}"
    ),
    parameter_mapping = parameters,
    initial_mapping = initials
)
