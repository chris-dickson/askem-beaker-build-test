---
layout: default
title: mira_model
parent: Contexts
nav_order: 1
has_toc: true
---

# mira_model

This context is used for editing models via [Mira](https://github.com/gyorilab/mira). On setup it expects a model `id` to be provided; unlike other contexts the key is always `id` and the value is the model `id`. For example:

```
{
  "id": "sir-model-id"
}
```

> **Note**: after setup, the model is accessible via the variable name `model`.

This context's LLM agent supports generic code generation using Mira with a specific focus on stratification. Users have the ability to ask to perform a stratification (e.g. _"Stratify my model into two cities: Boston and New York"_).

This context has 

This context has **4 custom message types**:

1. `save_amr_request`: takes in a `name` and saves the model as a new model in `hmi-server`, returning the new models `id`. Optionally takes in a `project_id` to save the model into the project.
2. `amr_to_templates`: converts AMR in JSON format to a Mira Template Model. Optionally accepts `model_name` which defaults to `model`--the variable where the AMR JSON is stored in context
3. `stratify_request`: stratifies the model based on `stratify_args` provided. Optionally accepts `model_name` which defaults to `model`--the variable where the AMR JSON is stored in context
4. `reset_request`: resets the `model` back to its original state
