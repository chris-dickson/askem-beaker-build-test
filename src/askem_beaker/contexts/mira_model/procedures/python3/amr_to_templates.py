from mira.sources.amr.petrinet import template_model_from_amr_json
from mira.modeling.amr.petrinet import AMRPetriNetModel


model_json = {{ var_name|default("model") }}
# model_tm = template_model_from_amr_json(model_json)
model_tm = model_json

# Define a new MIRA TemplateModel for each template in the model
templates_tm = []
templates_json = []
for i, __ in enumerate(model_tm.templates):
    t = copy.deepcopy(model_tm.templates[i])
    tm = TemplateModel(
        templates = [t],
        # parameters = {params_global[p]: params_concepts_global[params_global[p]] for p in t.get_parameter_names()},
        # initials = {vars_global[c.name]: inits_concepts_global[c.name] for c in t.get_concepts()},
        # annotations = Annotations(name = f"{t.name}{i}")
        parameters = {p: model_tm.parameters[p] for p in t.get_parameter_names()},
        initials = {v: model_tm.initials[v] for v in t.get_concept_names()},
        annotations = Annotations(name = f"{t.name}"),
        observables = {},
        time = model_tm.time
    )
    templates_tm.append(tm)
    templates_json.append(AMRPetriNetModel(Model(tm)).to_json())

# Define a new MIRA TemplateModel for each observable in the model
# concepts = model_tm.get_concepts_name_map()
# staticconcepts = [str(symb): concepts[str(symb)] for symb in model_tm.observables["N"].expression.free_symbols]
for obs_name, obs in model_tm.observables.items():
    tm = TemplateModel(
        templates = [
            StaticConcept(subject = model_tm.get_concepts_name_map()[str(symb)])
            for symb in obs.expression.free_symbols
        ],
        observables = {obs_name: obs},
        time = model_tm.time,
        annotations = Annotations(name = obs_name)
    )
    templates_tm.append(tm)
    templates_json.append(AMRPetriNetModel(Model(tm)).to_json())


{
  "templates": templates_json
}
