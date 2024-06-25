def add_observable(model, new_id: str, new_name: str, new_expression: str):
    """Add a new observable object to the template model

    Parameters
    ----------
    model : JSON
        The model as an AMR JSON
    new_id :
        The ID of the new observable to add
    new_name :
        The display name of the new observable to add
    new_expression :
        The expression of the new observable to add as a MathML XML string

    Returns
    -------
    : JSON
        The updated model as an AMR JSON
    """
    assert isinstance(model, TemplateModel)
    tm = model
    # Note that if an observable already exists with the given
    # key, it will be replaced
    rate_law_sympy = safe_parse_expr(new_expression, local_dict=_clash)
    new_observable = Observable(name=new_id, display_name=new_name,
                                expression=rate_law_sympy)
    tm.observables[new_id] = new_observable
    return tm

model = add_observable(
    model, 
    "{{ new_id }}", 
    "{{ new_name }}", 
    "{{ new_expression }}"
)