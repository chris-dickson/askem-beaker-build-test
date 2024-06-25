def replace_template_name(model, old_name: str, new_name: str):
    """Replace the name of a template in a given model."""
    if old_name not in {template.name: template for template in model.templates}:
        raise ValueError(f"Template with name {old_name} not found in the given model")

    for template in model.templates:
        if template.name == old_name:
            template.name = new_name
    return model

model = replace_template_name(model, '{{ old_name }}', '{{ new_name }}')
