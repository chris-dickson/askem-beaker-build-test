import json
import logging
import re

import requests
from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.jupyter_kernel_proxy import JupyterMessage

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


class MiraConfigEditAgent(BaseAgent):
    """
    LLM agent used for working with the Mira Modeling framework ("mira_model" package) in Python 3.
    This will be used to find pre-written functions which will be used to edit a model.

    A mira model is made up of multiple templates that are merged together like ...

    An example mira model will look like this when encoded in json:
    ```
    {
      "id": "foo",
      "bar": "foobar",
      ...
    }

    Instead of manipulating the model directly, the agent will always return code that will be run externally in a jupyter notebook.

    """

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        super().__init__(context, tools, **kwargs)

    @tool()
    async def get_parameters_initials(self, _type: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to see the names and values of the model configuration's parameters.
        Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
        You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
        No addtional text is needed in the response, just the code block.   

        Args:
            _type (str): either "parameters" or "initials" and determines whether to fetch values of the parameters or the initial conditions
        """
        loop.set_state(loop.STOP_SUCCESS)
        if _type == "parameters":
            code = agent.context.get_code("get_params")
        elif _type == "initials":
            code = agent.context.get_code("get_initials")
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def update_parameters(self, parameter_values: dict, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to update the model configuration parameter values.
        It takes in a dictionary where the key is the parameter name and the value is the new value in the form:

        ```
        {'param1': 10,
         'param_n: 2,
         ...}
        ```

        Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
        You MUST wrap the code with a line containing three backticks (```) before and after the generated code.
        No addtional text is needed in the response, just the code block.  

        Args:
            parameter_values (dict): the dictionary of parameter names and the values to update them with
        """
        # load in model config's parameters to use in comparison to the 
        # user provided parameters to update
        model_params = agent.context.model_config.parameters.keys()
        user_params = parameter_values['parameter_values'].keys()

        # check if any in user_params is not in model_params and return an error
        if not all(param in model_params for param in user_params):
            loop.set_state(loop.STOP_FATAL)
            error_message = f"It looks like you're trying to update parameter(s) that don't exist: " \
                            f"[{', '.join(param for param in user_params if param not in model_params)}]. " \
                            f"Please ensure you are updating a valid parameter: " \
                            f"[{', '.join(param for param in model_params)}]."
            return error_message

        loop.set_state(loop.STOP_SUCCESS)
        code = agent.context.get_code("update_params", {"parameter_values": parameter_values})
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
