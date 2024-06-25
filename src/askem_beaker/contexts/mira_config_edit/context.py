import copy
import datetime
import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import intercept

from .agent import MiraConfigEditAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

logger = logging.getLogger(__name__)

from mira.sources.amr import model_from_json; 

class MiraConfigEditContext(BaseContext):

    agent_cls = MiraConfigEditAgent

    model_config_id: Optional[str]
    model_config_json: Optional[str]
    model_config_dict: Optional[dict[str, Any]]
    var_name: Optional[str] = "model_config"

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]) -> None:
        self.reset()
        logger.error("initializing...")
        super().__init__(beaker_kernel, self.agent_cls, config)

    def reset(self):
        pass
        
    async def setup(self, context_info, parent_header):
        logger.error(f"performing setup...")
        self.config["context_info"] = context_info
        item_id = self.config["context_info"]["id"]
        item_type = self.config["context_info"].get("type", "model_config")
        logger.error(f"Processing {item_type} AMR {item_id} as a MIRA model")
        await self.set_model_config(
            item_id, item_type, parent_header=parent_header
        )

    async def post_execute(self, message):
        await self.send_mira_preview_message(parent_header=message.parent_header)

    async def set_model_config(self, item_id, agent=None, parent_header={}):
        self.config_id = item_id
        meta_url = f"{os.environ['HMI_SERVER_URL']}/model-configurations/as-configured-model/{self.config_id}"
        logger.error(f"Meta url: {meta_url}")
        self.amr = requests.get(meta_url,
                                          auth=(os.environ['AUTH_USERNAME'],
                                                os.environ['AUTH_PASSWORD'])
                                                ).json()
        logger.error(f"Succeeded in fetching configured model, proceeding.")
        self.schema_name = self.amr.get("header",{}).get("schema_name","petrinet")
        self.original_amr = copy.deepcopy(self.amr)
        if self.amr:
            await self.load_mira()
            self.model_config = model_from_json(self.amr)            
        else:
            raise Exception(f"Model config '{item_id}' not found.")
        await self.send_mira_preview_message(parent_header=parent_header)

    async def load_mira(self):
        command = "\n".join(
            [
                self.get_code("setup"),
                self.get_code("load_model", {
                    "var_name": self.var_name,
                    "model": self.amr,
                }),
            ]
        )
        print(f"Running command:\n-------\n{command}\n---------")
        await self.execute(command)        

    async def send_mira_preview_message(
        self, server=None, target_stream=None, data=None, parent_header={}
    ):
        try:
            preview = await self.evaluate(self.get_code("model_preview"), {"var_name": self.var_name, "schema_name": self.schema_name})
            content = preview["return"]
            self.beaker_kernel.send_response(
                "iopub", "model_preview", content, parent_header=parent_header
            )
        except Exception as e:
            raise

    @intercept()
    async def save_model_config_request(self, message):
        '''
        Updates the model configuration in place.
        '''
        content = message.content

        if self.schema_name == "regnet":
            unloader = f"template_model_to_regnet_json({self.var_name})"
        elif self.schema_name == "stockflow":
            unloader = f"template_model_to_stockflow_json({self.var_name})"
        else:
            unloader = f"template_model_to_petrinet_json({self.var_name})"
            
        new_model: dict = (
            await self.evaluate(unloader)
        )["return"]

        create_req = requests.put(
            f"{os.environ['HMI_SERVER_URL']}/model-configurations/as-configured-model/{self.config_id}", json=new_model,
                auth =(os.environ['AUTH_USERNAME'], os.environ['AUTH_PASSWORD'])
        )

        if create_req.status_code == 200:
            logger.error(f"Successfuly updated model config {self.config_id}")
        response_id = create_req.json()["id"]

        content = {"model_configuration_id": response_id}
        self.beaker_kernel.send_response(
            "iopub", "save_model_response", content, parent_header=message.header
        )
