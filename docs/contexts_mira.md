---
layout: default
title: mira
parent: Contexts
nav_order: 1
has_toc: true
---

# mira

This context is used for new development around [Mira](https://github.com/gyorilab/mira) with a specific focus on trying to generate new behavior with an LLM assistant based on Mira's documentation and examples. On setup, the context expects an object with a single key `models`, a list of objects containing `name` and `model_id`.:

```
{
    "models": [
        {
            "name": "model_1",
            "model_id": "501bb870-890c-4aaf-adce-d66d0080bb08"
        },
        {
            "name": "model_2",
            "model_id": "307a9ce9-88b1-437e-9026-dbf96af4d534"
        },
        {
            "name": "model_3",
            "model_id": "6242c648-c817-479a-833e-11f01bab78c7"
        }
    ]
}
```
## Custom Actions  
### `save_amr`

Message Payload:  
* `name`: string, name of the new model to save
* `model_var`: string, name of the variable containing a mira model; can be a newly created one or any of the ones loaded in context setup
* `project_id`: *optional*, will save the model to the given project if desired.

#### Save a new model to a given project:
```
{
  "name": "New SIR model with changes",
  "model_var": "sir_model",
  "project_id": "d59c00f3-aeb9-42ed-97bf-cc36c14cd008"
}
```

#### Save a new model to no specific project:
```
{
  "name": "New SIR model with changes",
  "model_var": "sir_model",
}
```

## Interactive Use

> **Note**: after setup, the models are accessible via the variable names corresponding to the given `name` field.

This context is built for LLM oriented natural language conversation. 

Some examples:

#### `Create an SIR model with ontological grounding.`

```python
from mira.metamodel import Concept, ControlledConversion, NaturalConversion, TemplateModel

# Define the concepts with ontological grounding
susceptible = Concept(name='susceptible population', identifiers={'ido': '0000514'})
infected = Concept(name='infected population', identifiers={'ido': '0000511'})
recovered = Concept(name='recovered population', identifiers={'ido': '0000592'})

# Define the transitions
infection = ControlledConversion(
    subject=susceptible,
    outcome=infected,
    controller=infected,
    rate_law='beta * susceptible_population * infected_population',
    name='infection'
)

recovery = NaturalConversion(
    subject=infected,
    outcome=recovered,
    rate_law='gamma * infected_population',
    name='recovery'
)

# Create the SIR model
sir_model = TemplateModel(templates=[infection, recovery])

# Display the model in JSON format
print(sir_model.json(indent=2))
```

#### `Compare the three models and visualize and display them.`

*(with the default context aoove, models named `model_1`, `model_2`, `model_3`)*

```python
from mira.metamodel.comparison import TemplateModelComparison, TemplateModelDelta
from mira.metamodel import get_dkg_refinement_closure
from IPython.display import display, Image

# Get the refinement function from the domain knowledge graph
dkg_refinement_closure = get_dkg_refinement_closure()
refinement_func = dkg_refinement_closure.is_ontological_child

# Create a comparison object for the three models
model_comparison = TemplateModelComparison(
    [model_1, model_2, model_3],
    refinement_func=refinement_func
)

# Generate a comparison graph for each pair of models and display them
comparison_1_2 = TemplateModelDelta(model_1, model_2, refinement_func)
comparison_1_2.draw_graph('comparison_1_2.png', args='-Grankdir=TB')
display(Image(filename='comparison_1_2.png'))

comparison_1_3 = TemplateModelDelta(model_1, model_3, refinement_func)
comparison_1_3.draw_graph('comparison_1_3.png', args='-Grankdir=TB')
display(Image(filename='comparison_1_3.png'))

comparison_2_3 = TemplateModelDelta(model_2, model_3, refinement_func)
comparison_2_3.draw_graph('comparison_2_3.png', args='-Grankdir=TB')
display(Image(filename='comparison_2_3.png'))
```