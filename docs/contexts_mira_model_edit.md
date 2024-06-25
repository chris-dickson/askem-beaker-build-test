---
layout: default
title: mira_model_edit
parent: Contexts
nav_order: 1
has_toc: true
---

# mira_model_edit

This context is used for editing models via [Mira](https://github.com/gyorilab/mira) with a specific focus on fine-grained state and transition manipulation. This context was created by Uncharted. On setup it expects a model `id` to be provided; unlike other contexts the key is always `id` and the value is the model `id`. For example:

```
{
  "id": "sir-model-id"
}
```

> **Note**: after setup, the model is accessible via the variable name `model`.

This context has **16 custom message types** 
These will provide codeblocks which often have documentation within them to be provided to the user

1. `reset_request`: resets the `model` back to its original state
2. `replace_template_name_request`: replaces the template `old_name` with `new_name`
3. `replace_state_name_request`: replaces the state's `old_name` with `new_name` for a given `model` and `template_name`
4. Add Template:
    `add_natural_conversion_template_request`
    `add_natural_production_template_request`
    `add_natural_degradation_template_request`
    `add_controlled_conversion_template_request`
    `add_controlled_production_template_request`
    `add_controlled_degradation_template_request`
5. `remove_template_request`: Removes an existing template from the model provided a `template_name`
6. `add_parameter_request`: Adds a new parameter to the model. 
7. `update_parameter_request` Updates an existing parameter in the model.
8. `add_observable_template_request` Add a new observable to the model.
9. `remove_observable_template_request` Remove an existing observable from the model.
10. `replace_ratelaw_request` update the value of a ratelaw in the model.
11. `amr_to_templates`: Breaks down an AMR into its template components.



# Sample agent questions and their corresponding tool:
# Adding templates:
1. Natural Conversion: 
    `Add a new transition from S to R with the name vaccine with the rate of v.`
    `Add a new transition from I to D. Name the transition unlucky and give it a rate of I*u`

2. Controlled Conversion: 
    `Add a new transition from S to R with the name vaccine with the rate of v. v depends on S`
    `Add a new transition from I to D. Name the transition unlucky that has a dependency on R. The rate is I*R*u`

3. Natural Production: 
    `Add a new transition from the transition rec to S with a rate of f.`
    `add a new transition (from nowhere) to S with a rate constant of f`

4. Controlled Production: 
    `Add a new transition from the transition rec to S with a rate of f. f depends on R. `
    `add a new transition (from nowhere) to S with a rate constant of f. The rate depends on R`

5. Natural Degredation: 
    `Add a new transition from state S to transition rec with a rate of v.`
    `add a new transition from S (to nowhere) with a rate constant of v`

6. Controlled Degredation: 
    `Add a new transition from S to rec with a rate of v. v depends on R.`
    `add a new transition from S (to nowhere) with a rate constant of v. The Rate depends on R`

# Observables:
1. `Add an observable titled noninf with the expression S+R.`
2. `Remove the noninf observable.`

# Renaming:
1. `Rename the state S to Susceptible in the infection transition.`
2. `Rename the transition infection to inf.`