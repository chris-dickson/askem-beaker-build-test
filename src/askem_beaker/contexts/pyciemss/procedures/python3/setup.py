import pyciemss
import os
import requests
from requests.auth import HTTPBasicAuth
import json, dill
import torch
import pandas as pd
import numpy as np
from typing import Dict, List

import pyciemss.visuals.plots as plots
import pyciemss.visuals.vega as vega
import pyciemss.visuals.trajectories as trajectories

from pyciemss.integration_utils.intervention_builder import (
    param_value_objective,
    start_time_objective,
)
from pyciemss.interfaces import optimize, sample

def obs_nday_average_qoi(
    samples: Dict[str, torch.Tensor], contexts: List, ndays: int = 7
) -> np.ndarray:
    """
    Return estimate of last n-day average of each sample.
    samples is is the output from a Pyro Predictive object.
    samples[VARIABLE] is expected to have dimension (nreplicates, ntimepoints)
    Note: last ndays timepoints is assumed to represent last n-days of simulation.
    """
    dataQoI = samples[contexts[0]].detach().numpy()
    return np.mean(dataQoI[:, -ndays:], axis=1)


def _result_fields() -> list[str]:
    result_exists = "result" in vars() or "result" in globals()
    if not (result_exists and isinstance(result, dict)):
        return []

    mapping = {
       "data": "result.csv", 
       "risk": "risk.json",
       "eval": "eval.csv",
       "inferred_parameters": "parameters.dill",
       "policy": "policy.json",
       "OptResults": "optimize_results.json", # excluding the optimize_results.dill for now.
       "visual": "visualization.json",
    }
    to_filename = lambda key: mapping[key] if key in result else None
    return [to_filename(key) for key in mapping.keys() if to_filename(key) is not None]
   
# adapted from the pyciemss-service
def _save_result(job_id, username, password):
    result_exists = "result" in vars() or "result" in globals()
    if not (result_exists and isinstance(result, dict)):
        return
    auth = HTTPBasicAuth(username, password)
    sim_results_url = os.environ["HMI_SERVER_URL"] + "/simulations/" + str(job_id)
    files = {}

    output_filename = "./result.csv"
    data_result = result.get("data", None)
    if data_result is not None:
        data_result.to_csv(output_filename, index=False)
        files[output_filename] = "result.csv"

    risk_result = result.get("risk", None)
    if risk_result is not None:
        # Update qoi (tensor) to a list before serializing with json.dumps
        for k, v in risk_result.items():
            risk_result[k]["qoi"] = v["qoi"].tolist()
        risk_json_obj = json.dumps(risk_result, default=str)
        json_obj = json.loads(risk_json_obj)
        json_filename = "./risk.json"
        with open(json_filename, "w") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=4)
        files[json_filename] = "risk.json"

    eval_output_filename = "./eval.csv"
    eval_result = result.get("quantiles", None)
    if eval_result is not None:
        eval_result.to_csv(eval_output_filename, index=False)
        files[eval_output_filename] = "eval.csv"

    params_filename = "./parameters.dill"
    params_result = result.get("inferred_parameters", None)
    if params_result is not None:
        with open(params_filename, "wb") as file:
            dill.dump(params_result, file)
        files[params_filename] = "parameters.dill"

    policy_filename = "./policy.json"
    policy = result.get("policy", None)
    if policy is not None:
        with open(policy_filename, "w") as file:
            json.dump(policy.tolist(), file)
        files[policy_filename] = "policy.json"

    results_filename = "./optimize_results.dill"
    results = result.get("OptResults", None)
    if results is not None:
        json_obj = json.loads(json.dumps(results, default=str))
        json_filename = "./optimize_result.json"
        with open(json_filename, "w") as f:
            json.dump(json_obj, f, ensure_ascii=False, indent=4)
        files[json_filename] = "optimize_results.json"

        with open(results_filename, "wb") as file:
            dill.dump(results, file)
        files[results_filename] = "optimize_results.dill"

    visualization_filename = "./visualization.json"
    viz_result = result.get("visual", None)
    if viz_result is not None:
        with open(visualization_filename, "w") as f:
            json.dump(viz_result, f, indent=2)
        files[visualization_filename] = "visualization.json"

    for location, handle in files.items():
        upload_url = f"{sim_results_url}/upload-url?filename={handle}"
        upload_response = requests.get(upload_url, auth=auth)
        presigned_upload_url = upload_response.json()["url"]

        with open(location, "rb") as f:
            upload_response = requests.put(presigned_upload_url, f)
            if upload_response.status_code >= 300:
                raise Exception(
                    (
                        "Failed to upload file to HMI "
                        f"(status: {upload_response.status_code}): {handle}"
                    )
                )

    return list(files.values())
