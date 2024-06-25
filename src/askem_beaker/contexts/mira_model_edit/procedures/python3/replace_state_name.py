def replace_state_name(model , template_name: str, old_name: str, new_name: str) -> TemplateModel:

    """
    Given a TemplateModel model and the old & new name of a state/concept therein, 
    1. if the old name doesn't exist, do nothing
    2. if the new name is unused, replace the name of that state/concept
    3. if the new name is used, replace the old-name concept by the new-name concept
    
    Apply same replacement to the rate laws, observable expressions, and initials.
    """

    # Check if concept with old name exists
    concepts_name_map = model.get_concepts_name_map()
    if old_name not in concepts_name_map:
        raise ValueError(f"State with name {old_name} not found in model.")
    
    # Check if concept with new name exists
    if new_name in concepts_name_map:
        new_concept = concepts_name_map[new_name]
        print(f"State with name {new_name} exists already in model and will replace state {old_name} everywhere.", UserWarning)

    # Check if old name is already used by a parameter or observable
    if old_name in model.observables.keys():
        raise ValueError(f"Name {old_name} already used by a model observable.")
    if old_name in model.parameters.keys():
        raise ValueError(f"Name {old_name} already used by a model parameter.")
        
    # Rename name of concept
    for template in model.templates:
        if template.name == template_name:
            if old_name in template.get_concept_names():
                for concept in template.get_concepts():
                    if concept.name == old_name: 

                        if new_name not in concepts_name_map:
                            concept.name = new_name
                        else:
                            for role in template.concept_keys:
                                if getattr(template, role).name == old_name:
                                    setattr(template, role, new_concept)

                template.rate_law = SympyExprStr(
                    template.rate_law.args[0].subs(
                        sympy.Symbol(old_name), sympy.Symbol(new_name))
                    )
    
    # Update observable expressions with new state name
    for observable in model.observables.values():
        if sympy.Symbol(old_name) in observable.expression.free_symbols:
            observable.expression = SympyExprStr(
                observable.expression.args[0].subs(
                    sympy.Symbol(old_name), sympy.Symbol(new_name))
                )
    
    # Ditto for initials
    if (old_name in model.initials) & (new_name not in model.initials):
        model.initials[new_name] = model.initials.pop(old_name)
        model.initials[new_name].concept.name = new_name
    if (old_name in model.initials) & (new_name in model.initials):
        __ = model.initials.pop(old_name)
    if (new_name not in model.initials):
        concept = model.get_concepts_name_map()[new_name]
        model.initials[new_name] = Initial(concept = concept, expression = sympy.Float(1))

    return model


model = replace_state_name(model, '{{ template_name }}', '{{ old_name }}', '{{ new_name }}')