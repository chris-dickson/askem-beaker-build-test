def remove_observable(model, removed_id: str):
    """Remove an observable from the template model

    Parameters
    ----------
    model : JSON
        The model as an AMR JSON
    removed_id :
        The ID of the observable to remove

    Returns
    -------
    : JSON
        The updated model as an AMR JSON
    """
    assert isinstance(model, TemplateModel)
    tm = model
    for obs, observable in copy.deepcopy(tm.observables).items():
        if obs == removed_id:
            tm.observables.pop(obs)
    return tm

model = remove_observable(model,"{{ remove_id }}")