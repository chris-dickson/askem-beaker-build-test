import codecs
import copy
import json
import datetime
import os
import requests
from base64 import b64encode
from typing import TYPE_CHECKING, Any, Dict

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import action

from .agent import PyCIEMSSAgent
from askem_beaker.utils import get_auth

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.agent import BaseAgent
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

import logging
logger = logging.getLogger(__name__)


class PyCIEMSSContext(BaseContext):

    agent_cls: "BaseAgent" = PyCIEMSSAgent

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]) -> None:
        self.auth = get_auth()
        super().__init__(beaker_kernel, self.agent_cls, config)

    async def setup(self, context_info: dict, parent_header):
        self.config["context_info"] = context_info
        await self.execute(self.get_code("setup"))
        if "model_config_id" in context_info:
            await self.set_model_config(context_info["model_config_id"], parent_header=parent_header)

    async def set_model_config(self, config_id, agent=None, parent_header=None):
        if parent_header is None: parent_header = {}
        self.config_id = config_id
        meta_url = f"{os.environ['HMI_SERVER_URL']}/model-configurations/as-configured-model/{self.config_id}"
        self.amr = requests.get(meta_url,
                                          auth=(os.environ['AUTH_USERNAME'],
                                                os.environ['AUTH_PASSWORD'])
                                                ).json()
        logger.info(f"Succeeded in fetching configured model, proceeding.")
        self.schema_name = self.amr.get("header",{}).get("schema_name","petrinet")
        self.original_amr = copy.deepcopy(self.amr)
        command = f"model = {self.amr}"
        print(f"Running command:\n-------\n{command}\n---------")
        await self.execute(command)        

    @action()
    async def get_optimize(self, message):
        code = self.get_code("optimize", message.content)
        self.send_response("iopub", "code_cell", {"code": code}, parent_header=message.header) 
        return code
    get_optimize._default_payload = "{}"

    @action()
    async def get_simulate(self, message):
        code = self.get_code("simulate", message.content)
        self.send_response("iopub", "code_cell", {"code": code}, parent_header=message.header) 
        return code
    get_simulate._default_payload = "{}"

    @action()
    async def save_results(self, message):
        code = self.get_code("save_results")
        response = await self.evaluate(code)
        return response["return"]
    save_results._default_payload = "{}"

    @action()
    async def save_results_to_hmi(self, message):
        post_url = os.environ["HMI_SERVER_URL"] + "/simulations"
        sim_type = message.content.get("sim_type", "simulate")
        auth = self.auth.requests_auth()
        response = await self.evaluate(
           f"_result_fields()" 
        )
        result_files = response["return"]
        payload = {
            "name": "PyCIEMSS Notebook Session",
            "execution_payload": {},
            "result_files": result_files,
            "type": sim_type,
            "status": "complete",
            "engine": "ciemss",
        }
        response = requests.post(post_url, json=payload, auth=auth)
        if response.status_code >= 300:
            raise Exception(
                (
                    "Failed to create simulation on TDS "
                    f"(reason: {response.reason}({response.status_code}) - {json.dumps(payload)}"
                )
            )

        sim_id = response.json()["id"]
        sim_url = post_url + f"/{sim_id}"
        payload = requests.get(sim_url, auth=auth).json()
        result_files = await self.evaluate(
           f"_save_result('{sim_id}', '{auth.username}', '{auth.password}')" 
        )
        assert isinstance(result_files["return"], list)

        if "result.csv" not in result_files["return"]:
            return {
                "simulation_id": sim_id,
                "result_files": result_files["return"]
            }


        dataset_payload = {
            "name": "Beaker Kernel Results",
            "temporary": False,
            "publicAsset": True,
            "description": "Dataset created in the Beaker Kernel PyCIEMSS Context",
            "fileNames": [
                "result.csv"
            ],
            "columns": [
            ],
            "metadata": {},
            "source": "beaker-kernel",
            "grounding": {
                "identifiers": {},
                "context": {}
            }
        }

        dataservice_url = os.environ["HMI_SERVER_URL"] + "/datasets"
        create_req = requests.post(dataservice_url, auth=auth, json=dataset_payload)
        dataset_id = create_req.json()["id"]
        dataset_url = dataservice_url + f"/{dataset_id}"
        data_url_req = requests.get(f"{dataset_url}/upload-url?filename=result.csv", auth=auth)
        data_url = data_url_req.json().get('url', None)
        code = self.get_code(
            "df_save_as",
            {
                "data_url": data_url,
            }
        )
        kernel_response = await self.execute(code) # TODO: Check error

        add_asset_url = os.environ["HMI_SERVER_URL"] + f"/projects/{message.content['project_id']}/assets/dataset/{dataset_id}"
        response = requests.post(add_asset_url, auth=auth)
        if response.status_code >= 300:
            raise Exception(
                (
                    "Failed to add dataset as asset ({add_asset_url}) "
                    f"(reason: {response.reason}({response.status_code}) - {json.dumps(payload)}"
                )
            )

        return {
            "dataset_id": dataset_id,
            "simulation_id": sim_id,
        }

    save_results_to_hmi._default_payload = '{\n\t"project_id": "a22f4865-c979-4ca2-aae0-5c9afc81b72a"\n}'



