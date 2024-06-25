---
layout: default
title: decapodes
parent: Contexts
nav_order: 1
has_toc: true
---

# decapodes

This context is used for [Decapode](https://algebraicjulia.github.io/Decapodes.jl/dev/) model editing in Julia. On setup it expects a model `id` and a variable name to be provided. For example here `halfar` will be the name of the variable for the model in the context and `ice_dynamics-id` is the `id` of the correpsonding model in `hmi-server`:

```
{
  "halfar": "ice_dynamics-id"
}
```

This context has **4 custom message types**:

1. `compile_expr`: this takes in a `declaration` and compiles it
2. `save_amr_request`: accepts a `header` and saves the decapode AMR model; returns the new model `id` in `hmi-server`
3. `construct_amr`: this builds an AMR container for the decapode and can accept a `name`, `description`, `id`, 
4. `reset_request`: accepts a `model_name`