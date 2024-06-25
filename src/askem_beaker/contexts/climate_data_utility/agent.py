import json
import logging
import re
from typing import Optional
import codecs

import pandas
import matplotlib.pyplot as plt
import xarray as xr

from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, is_tool, tool, toolset

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext


logger = logging.getLogger(__name__)


@toolset()
class ClimateDataUtilityToolset:
    """Toolset for ClimateDataUtility context"""

    @tool()
    async def detect_resolution(self, filepath: str, geo_columns: object, agent: AgentRef) -> str:
        """
        This function should be used to detect the resolution of a dataset.
        This can be used if the user doesn't know the resolution or if you are regridding a dataset and don't know a starting resolution.
        The resolution can further be used to make informed decisions about the scale multiplier to use for regridding.

        The dataset should have some geographical data in it in the form of a latitude and longitude column.

        Args:
            filepath (str): The filepath to the dataset to open.
            geo_columns (object): The names of the geographical columns in the dataset. This is an optional argument for this tool.
                This is an object with the keys 'lat_column' and 'lon_column'.
                The 'lat_column' key should have the name of the latitude column and the 'lon_column' key should have the name of the longitude column.

        Returns:
            str: Returned description of the resolution of the dataset.

        You should show the user the result after this function runs.
        """

        code = agent.context.get_code(
            "cartwright_res_detect",
            {
                "filepath": filepath,
                "geo_columns": geo_columns,
            },
        )
        result = await agent.context.evaluate(
            code,
            parent_header={},
        )

        resolution_result = result.get("return")

        return resolution_result

    @tool()
    async def regrid_dataset(
        self,
        dataset: str,
        target_resolution: tuple,
        agent: AgentRef,
        loop: LoopControllerRef,
        aggregation: Optional[str] = "interp_or_mean",
    ) -> str:
        """
        This tool should be used to show the user code to regrid a netcdf dataset with detectable geo-resolution.

        If a user asks to regrid a dataset, use this tool to return them code to regrid the dataset.

        If you are given a netcdf dataset, use this tool instead of any other regridding tool.

        If you are asked about what is needed to regrid a dataset, please provide information about the arguments of this tool.

        Args:
            dataset (str): The name of the dataset instantiated in the jupyter notebook.
            target_resolution (tuple): The target resolution to regrid to, e.g. (0.5, 0.5). This is in degrees longitude and latitude.
            aggregation (Optional): The aggregation function to be used in the regridding. The options are as follows:
                'conserve'
                'min'
                'max'
                'mean'
                'median'
                'mode'
                'interp_or_mean'
                'nearest_or_mode'

        Returns:
            str: Status of whether or not the dataset has been persisted to the HMI server.
        """

        loop.set_state(loop.STOP_SUCCESS)
        code = agent.context.get_code(
            "flowcast_regridding",
            {
                "dataset": dataset,
                "target_resolution": target_resolution,
                "aggregation": aggregation,
            },
        )

        result = json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

        return result

    @tool()
    async def get_netcdf_plot(
        self,
        dataset_variable_name: str,
        agent: AgentRef,
        loop: LoopControllerRef,
        plot_variable_name: Optional[str] = None,
        lat_col: Optional[str] = "lat",
        lon_col: Optional[str] = "lon",
        time_slice_index: Optional[int] = 1,
    ) -> str:
        """
        This function should be used to get a plot of a netcdf dataset.

        This function should also be used to preview any netcdf dataset.

        If the user asks to plot or preview a dataset, use this tool to return plotting code to them.

        You should also ask if the user wants to specify the optional arguments by telling them what each argument does.

        Args:
            dataset_variable_name (str): The name of the dataset instantiated in the jupyter notebook.
            plot_variable_name (Optional): The name of the variable to plot. Defaults to None.
                If None is provided, the first variable in the dataset will be plotted.
            lat_col (Optional): The name of the latitude column. Defaults to 'lat'.
            lon_col (Optional): The name of the longitude column. Defaults to 'lon'.
            time_slice_index (Optional): The index of the time slice to visualize. Defaults to 1.

        Returns:
            str: The code used to plot the netcdf.
        """

        loop.set_state(loop.STOP_SUCCESS)
        plot_code = agent.context.get_code(
            "get_netcdf_plot",
            {
                "dataset": dataset_variable_name,
                "plot_variable_name": plot_variable_name,
                "lat_col": lat_col,
                "lon_col": lon_col,
                "time_slice_index": time_slice_index,
            },
        )

        result = json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": plot_code.strip(),
            }
        )

        return result


class ClimateDataUtilityAgent(BaseAgent):
    """
    You are assisting us in modifying geo-temporal datasets.

    The main things you are going to do are regridding spatial datasets, temporally rescaling datasets, and clipping the extent of geo-temporal datasets.

    If you don't have the details necessary to use a tool, you should use the ask_user tool to ask the user for them.

    """

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        tools = [ClimateDataUtilityToolset]
        super().__init__(context, tools, **kwargs)
