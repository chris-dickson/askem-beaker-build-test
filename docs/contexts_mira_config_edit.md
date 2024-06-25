---
layout: default
title: mira_config_edit
parent: Contexts
nav_order: 1
has_toc: true
---

# mira_config_edit

This context is used for editing model configurations via [Mira](https://github.com/gyorilab/mira). It accesses the `model` aspect of a configuration and loads it as a Mira Template Model for editing. On setup it expects a model configuration `id` to be provided; unlike other contexts the key is always `id` and the value is the model configuration `id`. For example:

```
{
  "id": "sir-model-config-id"
}
```

> **Note**: after setup, the model configuration is accessible via the variable name `model_config`.

This context's LLM agent supports two key capabilities: a user can ask for the current parameter values or initial condition values and the user can ask to update either of these. In both instances the AI assistant generates **code** for the user to execute that performs the inspection/update procedure so that the human is always in the loop.

This context has **1 custom message types**:

1. `save_model_config_request`: this does not require arguments; it simply executes a `PUT` on the model configuration to update it in place based on the operations performed in the context.