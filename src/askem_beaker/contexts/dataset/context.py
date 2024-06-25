import codecs
import copy
import datetime
import os
import requests
from base64 import b64encode
from typing import TYPE_CHECKING, Any, Dict

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import intercept

from .agent import DatasetAgent
from askem_beaker.utils import get_auth

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.agent import BaseAgent
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

import logging
logger = logging.getLogger(__name__)


class DatasetContext(BaseContext):

    agent_cls: "BaseAgent" = DatasetAgent

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]) -> None:
        self.auth = get_auth()
        self.asset_map = {}
        super().__init__(beaker_kernel, self.agent_cls, config)

    async def setup(self, context_info: dict, parent_header):
        self.config["context_info"] = context_info
        await self.set_assets(self.config["context_info"], parent_header=parent_header)

    async def post_execute(self, message):
        await self.update_asset_map(parent_header=message.parent_header)
        await self.send_df_preview_message(parent_header=message.parent_header)

    async def set_assets(self, assets, parent_header={}):
        self.asset_map = assets
        for var_name, asset_item in assets.items():
            if isinstance(asset_item, str):
                asset_id = asset_item
                asset_type = "dataset"
                self.asset_map[var_name] = {
                    "id": asset_id,
                    "asset_type": asset_type,
                }
            elif isinstance(asset_item, dict):
                asset_id = asset_item["id"]
                asset_type = asset_item.get("asset_type", "dataset")
            else:
                raise ValueError("Unable to parse dataset mapping")

            meta_url = f"{os.environ['HMI_SERVER_URL']}/{asset_type}s/{asset_id}"
            asset_info_req = requests.get(meta_url, auth=self.auth.requests_auth())
            if asset_info_req.status_code == 404:
                raise Exception(f"Dataset '{asset_id}' not found.")
            asset_info = asset_info_req.json()
            if asset_info:
                self.asset_map[var_name]["info"] = asset_info
            else:
                raise Exception(f"{asset_type.capitalize()} '{asset_id}' not able to be loaded.")
        await self.load_dataframes()
        await self.send_df_preview_message(parent_header=parent_header)

    async def load_dataframes(self):
        var_map = {}
        for var_name, df_obj in self.asset_map.items():
            asset_type = df_obj.get("asset_type", "dataset")

            if asset_type != "dataset":
                filename = df_obj["info"].get("resultFiles", [])[0]
            else:
                filename = df_obj["info"].get("fileNames", [])[0]

            meta_url = f"{os.environ['HMI_SERVER_URL']}/{asset_type}s/{df_obj['id']}"
            url = f"{meta_url}/download-url?filename={filename}"
            data_url_req = requests.get(
                url=url,
                auth=self.auth.requests_auth(),
            )
            data_url = data_url_req.json().get("url", None)
            var_map[var_name] = data_url
        command = "\n".join(
            [
                self.get_code("setup"),
                self.get_code("load_df", {"var_map": var_map, "auth": self.auth}),
            ]
        )
        await self.execute(command)
        await self.update_asset_map()

    def reset(self):
        self.asset_map = {}

    async def send_df_preview_message(
        self, server=None, target_stream=None, data=None, parent_header={}
    ):
        preview = {
            var_name: {
                "name": df.get("name"),
                "headers": df.get("columns"),
                "csv": df.get("head"),
            }
            for var_name, df in self.asset_map.items()
        }
        self.beaker_kernel.send_response(
            "iopub", "dataset", preview, parent_header=parent_header
        )
        return data

    async def update_asset_map(self, parent_header={}):
        code = self.get_code("df_info")
        df_info_response = await self.evaluate(
            code,
            parent_header=parent_header,
        )
        df_info = df_info_response.get('return')
        for var_name, info in df_info.items():
            if var_name in self.asset_map:
                self.asset_map[var_name].update(info)
            else:
                self.asset_map[var_name] = {
                    "name": f"User created dataframe '{var_name}'",
                    "description": "",
                    **info,
                }

    async def auto_context(self):
        intro = f"""
You are an analyst whose goal is to help with scientific data analysis and manipulation in {self.metadata.get("name", "a Jupyter notebook")}.

You are working with the following dataset(s):
"""
        outro = f"""
Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate or visualize the dataset, use the generate_code tool.
"""
        dataset_blocks = []
        for var_name, dataset_obj in self.asset_map.items():
            dataset_info = dataset_obj.get("info", {})
            dataset_description = await self.describe_dataset(var_name)
            dataset_blocks.append(f"""
Name: {dataset_info.get("name", "User defined dataset")}
Variable: {var_name}
Description: {dataset_info.get("description", "")}

The dataset has the following structure:
--- START ---
{dataset_description}
--- END ---
""")
        result = "\n".join([intro, *dataset_blocks, outro])
        return result

    async def describe_dataset(self, var_name) -> str:
        """
        Inspect the dataset and return information and metadata about it.

        This should be used to answer questions about the dataset, including information about the columns,
        and default parameter values and initial states.


        Returns:
            str: a textual representation of the dataset
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.

        df_info = self.asset_map.get(var_name, None)
        if not df_info:
            return None
        output = f"""
Dataframe head:
{df_info["head"][:15]}


Columns:
{df_info["columns"]}


datatypes:
{df_info["datatypes"]}


Statistics:
{df_info["statistics"]}
"""
        return output

    @intercept()
    async def download_dataset_request(self, message):
        content = message.content
        var_name = content.get("var_name", "df")
        # TODO: Collect any options that might be needed, if they ever are

        # TODO: This doesn't work very well. Is very slow to encode, and transfer all of the required messages multiple times proxies through the proxy kernel.
        # We should find a better way to accomplish this if it's needed.
        code = self.get_code("df_download", {"var_name": var_name})
        df_response = await self.evaluate(code)
        df_contents = df_response.get("stdout_list")
        self.beaker_kernel.send_response(
            "iopub",
            "download_response",
            {
                "data": [
                    codecs.encode(line.encode(), "base64").decode()
                    for line in df_contents
                ]
            },
        )  # , parent_header=parent_header)

    @intercept()
    async def save_dataset_request(self, message):
        content = message.content

        parent_dataset_id = content.get("parent_dataset_id")
        new_name = content.get("name")
        filename = content.get("filename", None)
        var_name = content.get("var_name", "df")
        dataservice_url = os.environ["HMI_SERVER_URL"]

        if filename is None:
            filename = "dataset.csv"

        parent_url = f"{dataservice_url}/datasets/{parent_dataset_id}"
        parent_dataset = requests.get(parent_url, auth=self.auth.requests_auth()).json()
        if not parent_dataset:
            raise Exception(f"Unable to locate parent dataset '{parent_dataset_id}'")

        new_dataset = copy.deepcopy(parent_dataset)
        del new_dataset["id"]
        new_dataset["name"] = new_name
        new_dataset["description"] += f"\\nTransformed from dataset '{parent_dataset['name']}' ({parent_dataset['id']}) at {datetime.datetime.utcnow().strftime('%c %Z')}"
        new_dataset["fileNames"] = [filename]
        #clear the columns field on the new dataset as there was likely a change to either the columns or the data. HMI-Server will deal with regenerating this.
        new_dataset["columns"] = []

        import pprint
        logger.error(f"new dataset: {pprint.pformat(new_dataset)}")
        create_req = requests.post(f"{dataservice_url}/datasets", auth=self.auth.requests_auth(), json=new_dataset)
        new_dataset_id = create_req.json()["id"]
        logger.error(f"new dataset: {pprint.pformat(create_req.json())}")

        new_dataset["id"] = new_dataset_id
        new_dataset_url = f"{dataservice_url}/datasets/{new_dataset_id}"
        data_url_req = requests.get(f"{new_dataset_url}/upload-url?filename={filename}", auth=self.auth.requests_auth())
        data_url = data_url_req.json().get('url', None)

        code = self.get_code(
            "df_save_as",
            {
                "var_name": var_name,
                "data_url": data_url,
            }
        )
        df_response = await self.execute(code)

        if df_response:
            self.beaker_kernel.send_response(
                "iopub",
                "save_dataset_response",
                {
                    "dataset_id": new_dataset_id,
                    "filename": filename,
                    "parent_dataset_id": parent_dataset_id,
                },
            )
