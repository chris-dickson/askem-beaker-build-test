def update_parameter(model, updated_id: str, replacement_value=None):
    """
    Substitute every instance of the parameter with the given replacement_value.
    If replacement_value is none, substitute the parameter with 0.

    Parameters
    ----------
    model : JSON
        The model as an AMR JSON
    updated_id :
        The ID of the parameter to update
    replacement_value :
        The value to replace the parameter with (optional)

    Returns
    -------
    : JSON
        The updated model as an AMR JSON
    """
    assert isinstance(model, TemplateModel)
    tm = model
    if replacement_value:
        tm.substitute_parameter(updated_id, replacement_value)
    else:
        tm.eliminate_parameter(updated_id)

    for initial in tm.initials.values():
        if replacement_value:
            initial.substitute_parameter(updated_id, replacement_value)
        else:
            initial.substitute_parameter(updated_id, 0)
    return tm


model = update_parameter(model=model, updated_id='{{ updated_id }}', replacement_value={{ replacement_value }})