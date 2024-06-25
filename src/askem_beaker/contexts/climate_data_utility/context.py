import logging
import os
from typing import TYPE_CHECKING, Any, Dict

from archytas.tool_utils import LoopControllerRef

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.subkernels.python import PythonSubkernel
from beaker_kernel.lib.utils import intercept

from .agent import ClimateDataUtilityAgent

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.agent import BaseAgent
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

logger = logging.getLogger(__name__)


class ClimateDataUtilityContext(BaseContext):
    slug = "climate_data_utility"
    agent_cls: "BaseAgent" = ClimateDataUtilityAgent
    dataset_map: Dict[str, Any]

    def __init__(
        self,
        beaker_kernel: "LLMKernel",
        config: Dict[str, Any],
    ) -> None:
        self.climate_data_utility__functions = {}
        self.config = config
        self.dataset_map = {}
        super().__init__(beaker_kernel, self.agent_cls, config)
        if not isinstance(self.subkernel, PythonSubkernel):
            raise ValueError("This context is only valid for Python.")

    def get_auth(self) -> tuple[str, str]:
        return (os.getenv("AUTH_USERNAME", ""), os.getenv("AUTH_PASSWORD", ""))

    async def setup(self, context_info, parent_header):
        self.config["context_info"] = context_info 
        for name, dataset in self.config["context_info"].items():
            dataset_id = dataset.get("hmi_dataset_id", None)
            filename = dataset.get("filename", None)
            if dataset_id is None or filename is None:
                logging.error(f"failed to download dataset from initial context: {dataset}")
                return
            await self.download_dataset(name, dataset_id, filename)

    def reset(self):
        self.dataset_map = {}

    async def auto_context(self):
        intro = f"""
    You are a software engineer working on a climate dataset operations tool in a Jupyter notebook.

    Your goal is to help users perform various operations on climate datasets, such as regridding NetCDF datasets and plotting/previewing NetCDF files. 
    Additionally, the tools provide functionality to retrieve datasets from a storage server.

    Please provide assistance to users with their queries related to climate dataset operations.

    Remember to provide accurate information and avoid guessing if you are unsure of an answer.
    """

        return intro

    @intercept()
    async def download_dataset_request(self, message):
        """
        This is used to download a dataset from the HMI server.
        """

        content = message.content
        uuid = content.get("uuid")
        filename = content.get("filename")
        if filename is None:
            filename = f"{uuid}.nc"
        variable_name = content.get("variable_name") or "dataset_" + str(len(self.dataset_map))

        await self.download_dataset(variable_name, uuid, filename)

    async def download_dataset(self, variable_name, hmi_dataset_id, filename):
        code = self.get_code(
            "hmi_dataset_download",
            {"auth": self.get_auth(), "id": hmi_dataset_id, "filename": filename, "variable_name": variable_name},
        )

        self.dataset_map[variable_name] = {"id": hmi_dataset_id, "variable_name": variable_name}
        await self.beaker_kernel.execute(
            code,
            parent_header={},
        )

    @intercept()
    async def save_dataset_request(self, message):
        """
        This tool is used to save a dataset to the HMI server.
        The 'dataset' argument is the variable name of the dataset to save in the notebook environment.
        """

        content = message.content
        dataset = content.get("dataset")
        new_dataset_filename = content.get("filename")

        create_code = self.get_code(
            "hmi_create_dataset",
            {
                "identifier": new_dataset_filename,
            },
        )
        create_response = await self.evaluate(
            create_code,
            parent_header={},
        )

        create_response_object = create_response.get("return")

        if isinstance(create_response_object, str):
            return create_response_object

        id = create_response_object.get("id")

        persist_code = self.get_code(
            "hmi_dataset_put",
            {
                "data": dataset,
                "id": id,
                "filename": f"{new_dataset_filename}",
                "auth": self.get_auth(),
            },
        )

        result = await self.evaluate(
            persist_code,
            parent_header={},
        )

        persist_status = result.get("return")

        self.beaker_kernel.send_response(
            "iopub",
            "save_dataset_response",
            {"dataset_create_status": create_response_object, "file_upload_status": persist_status},
        )
