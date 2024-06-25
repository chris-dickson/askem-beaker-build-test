---
layout: default
title: dataset
parent: Contexts
nav_order: 1
has_toc: true
---

# dataset

This context is used for ad hoc manipulation of datasets in either Python, Julia, or R. These manipulations might include basic data munging or more complex tasks. On setup it expects a dataset map to be provided where the key is the variable name for the dataet in the context and the value is the dataset ID in the `hmi-server`. For example:

```
{
  "df_hosp": "truth-incident-hospitalization",
  "df_cases": "truth-incident-case"
} 
```

Note that multiple datasets may be loaded at a given time. This context has **2 custom message types**:

1. `download_dataset_request`: stream a download of the desired dataset as specified by `var_name` (e.g. `df`).
2. `save_dataset_request`: save a dataset as specified by `var_name` (e.g. `df`), a `name` for the new dataset, the `parent_dataset_id` and an optional `filename` and create the new dataset. The response will include the `id` of the new dataset in `hmi-server`.