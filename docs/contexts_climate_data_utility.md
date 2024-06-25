---
layout: default
title: climate_data_utility
parent: Contexts
nav_order: 1
has_toc: true
---

# climate_data_utility

This context is used for handling climate datasets integrated with the HMI server. 

```
{
    "mrros_dataset": {
        "hmi_dataset_id": "149efd94-dc91-4673-9245-443ad61276ea", 
        "filename": "cmip6-6e565455-9589-4d7c-8960-18c47ed6b9b7.nc"
    },
    "secondary_dataset": {
        "hmi_dataset_id": "149efd94-dc91-4673-9245-443ad61276ea", 
        "filename": "cmip6-6e565455-9589-4d7c-8960-18c47ed6b9b7.nc"
    }
}
```

Dataset IDs and filenames should be from the HMI server. 

> **Note**: after setup, the datasets are accessible via the variable names provided as dictionary keys.

This context's LLM agent supports generic code generation with climate datasets with a focus on regridding and downscaling. Users have the ability to ask to perform a downscaling operation (e.g. _"regrid dataset named mrros dataset to a resolution of 0.1, 0.1 with interpolation aggregation"_). Other operations include plotting the given dataset.

This context has **2 custom message types**:

1. `download_dataset_request`: Downloads a dataset from the HMI server. Takes in the parameters `uuid`, an HMI dataset ID, and `filename`, the target filename to download. Optionally accepts `variable_name` which is where to store it, if not provided, it will incrementally create `dataset_0`, `dataset_1`... `dataset_X`.
3. `save_dataset_request`: Takes in `dataset` and `filename` and uploads the given dataset with the filename to the HMI server.

