
import copy
import datetime
import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict, Optional

import requests

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import intercept

from .agent import MiraModelAgent
from askem_beaker.utils import get_auth

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

logger = logging.getLogger(__name__)


class MiraModelContext(BaseContext):

    agent_cls = MiraModelAgent

    model_id: Optional[str]
    model_json: Optional[str]
    model_dict: Optional[dict[str, Any]]
    var_name: Optional[str] = "model"
    schema_name: Optional[str] = "petrinet"

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]) -> None:
        self.reset()
        self.auth = get_auth()
        super().__init__(beaker_kernel, self.agent_cls, config)

    async def setup(self, context_info, parent_header):
        self.config["context_info"] = context_info
        item_id = context_info["id"]
        item_type = context_info.get("type", "model")
        print(f"Processing {item_type} AMR {item_id} as a MIRA model")
        await self.set_model(
            item_id, item_type, parent_header=parent_header
        )

    async def post_execute(self, message):
        await self.send_mira_preview_message(parent_header=message.parent_header)

    async def set_model(self, item_id, item_type="model", agent=None, parent_header={}):
        if item_type == "model":
            self.model_id = item_id
            self.config_id = "default"
            meta_url = f"{os.environ['HMI_SERVER_URL']}/models/{self.model_id}"
            self.amr = requests.get(meta_url, auth=self.auth.requests_auth()).json()
            self.schema_name = self.amr.get("header",{}).get("schema_name","petrinet")
        elif item_type == "model_config":
            self.config_id = item_id
            meta_url = f"{os.environ['HMI_SERVER_URL']}/model_configurations/{self.config_id}"
            self.configuration = requests.get(meta_url, auth=self.auth.requests_auth()).json()
            self.model_id = self.configuration.get("model_id")
            self.amr = self.configuration.get("configuration")
            self.schema_name = self.amr.get("header",{}).get("schema_name","petrinet")
        self.original_amr = copy.deepcopy(self.amr)
        if self.amr:
            await self.load_mira()
        else:
            raise Exception(f"Model '{item_id}' not found.")
        await self.send_mira_preview_message(parent_header=parent_header)

    async def load_mira(self):
        model_url = f"{os.environ['HMI_SERVER_URL']}/models/{self.model_id}"
        command = "\n".join(
            [
                self.get_code("setup"),
                self.get_code("load_model", {
                    "var_name": self.var_name,
                    "model_url": model_url,
                    "auth_header": self.auth.auth_header(),
                }),
            ]
        )
        print(f"Running command:\n-------\n{command}\n---------")
        await self.execute(command)

    def reset(self):
        self.model_id = None

    async def auto_context(self):
        return f"""You are an scientific modeler whose goal is to use the MIRA modeling library to manipulate and stratify Petrinet models in Python.

You are working on a Petrinet model named: {self.amr.get('name')}

The description of the model is:
{self.amr.get('description')}

The model has the following structure:
--- START ---
{await self.model_structure()}
--- END ---

Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate, stratify, or visualize the model, use the generate_code tool.
"""

    async def model_structure(self) -> str:
        """
        Inspect the model and return information and metadata about it.

        This should be used to answer questions about the model, including information about the states, populations, transistions, etc.


        Returns:
            str: a textual representation of the model
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.
        amr = (
            await self.evaluate(self.get_code("model_to_json", {"var_name": self.var_name, "schema_name": self.schema_name}))
        )["return"]
        return json.dumps(amr, indent=2)

    async def send_mira_preview_message(
        self, server=None, target_stream=None, data=None, parent_header={}
    ):
        try:

            preview = await self.evaluate(self.get_code("model_preview", {"var_name": self.var_name, "schema_name": self.schema_name}))
            content = preview["return"]
            self.beaker_kernel.send_response(
                "iopub", "model_preview", content, parent_header=parent_header
            )
        except Exception as e:
            raise

    @intercept()
    async def save_amr_request(self, message):
        content = message.content

        new_name = content.get("name")
        project_id = content.get("project_id")

        if self.schema_name == "regnet":
            unloader = f"template_model_to_regnet_json({self.var_name})"
        elif self.schema_name == "stockflow":
            unloader = f"template_model_to_stockflow_json({self.var_name})"
        else:
            unloader = f"template_model_to_petrinet_json({self.var_name})"

        new_model: dict = (
            await self.evaluate(unloader)
        )["return"]

        original_name = new_model.get("name", "None")
        original_model_id = self.model_id

        # Deprecated: Handling both new and old model formats

        if "header" in new_model:
            new_model["header"]["name"] = new_name
            new_description = new_model.get("header", {}).get("description", "") + f"\nTransformed from model '{original_name}' ({original_model_id}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
            new_model["header"]["description"] = new_description
            if getattr(self, "configuration", None) is not None:
                new_model["header"][
                    "description"
                ] += f"\nfrom base configuration '{self.configuration.get('name')}' ({self.configuration.get('id')})"
        else:
            new_model["name"] = new_name
            new_model[
                "description"
            ] += f"\nTransformed from model '{original_name}' ({original_model_id}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
            if getattr(self, "configuration", None) is not None:
                new_model[
                    "description"
                ] += f"\nfrom base configuration '{self.configuration.get('name')}' ({self.configuration.get('id')})"

        create_req = requests.post(
            f"{os.environ['HMI_SERVER_URL']}/models", json=new_model,
            auth=self.auth.requests_auth(),
        )
        new_model_id = create_req.json()["id"]

        if project_id is not None:
            update_req = requests.post(
                f"{os.environ['HMI_SERVER_URL']}/projects/{project_id}/assets/model/{new_model_id}",
                auth=self.auth.requests_auth(),
            )

        content = {"model_id": new_model_id}
        self.beaker_kernel.send_response(
            "iopub", "save_model_response", content, parent_header=message.header
        )


    @intercept()
    async def amr_to_templates(self, message):
        content = message.content
        model_name = content.get("model_name", "model")

        code = self.get_code("amr_to_templates", {
            "var_name": model_name
        })
        result = (await self.evaluate(code))["return"]

        content = {
            "success": True,
            "templates": result["templates"]
        }
        self.beaker_kernel.send_response(
            "iopub", "amr_to_templates_response", content, parent_header=message.header
        )


    @intercept()
    async def stratify_request(self, message):
        content = message.content

        model_name = content.get("model_name", "model")
        stratify_args = content.get("stratify_args", None)
        if stratify_args is None:
            # Error
            logger.error("stratify_args must be set on stratify requests.")
            self.beaker_kernel.send_response(
                "iopub", "error", {
                    "ename": "ValueError",
                    "evalue": "stratify_args must be set on stratify requests",
                    "traceback": [""]
                }, parent_header=message.header
            )
            return
        stratify_code = self.get_code("stratify", {
            "var_name": model_name,
            "stratify_kwargs": repr(stratify_args),
            "schema_name": self.schema_name
        })
        stratify_result = await self.execute(stratify_code)

        content = {
            "success": True,
            "executed_code": stratify_result["parent"].content["code"],
        }

        self.beaker_kernel.send_response(
            "iopub", "stratify_response", content, parent_header=message.header
        )
        await self.send_mira_preview_message(parent_header=message.header)


    @intercept()
    async def reset_request(self, message):
        content = message.content

        model_name = content.get("model_name", "model")
        reset_code = self.get_code("reset", {
            "var_name": model_name,
        })
        reset_result = await self.execute(reset_code)

        content = {
            "success": True,
            "executed_code": reset_result["parent"].content["code"],
        }

        self.beaker_kernel.send_response(
            "iopub", "reset_response", content, parent_header=message.header
        )
        await self.send_mira_preview_message(parent_header=message.header)
