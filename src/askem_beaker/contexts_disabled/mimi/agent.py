import json
import logging
import re

from archytas.tool_utils import AgentRef, LoopControllerRef, tool, toolset

from beaker_kernel.lib.context import BaseContext
logger = logging.getLogger(__name__)
from .new_base_agent import NewBaseAgent
from typing import List

@toolset()
class Toolset:
    """Toolset for our context"""

#     @tool(autosummarize=True)
    async def search_installed_packages(self, name: str, agent: AgentRef) -> str:
        """
        Search installed packages using a naive match

        E.g. Searching using the name "Data" might return ["DataFrames"]

        Args:
            name (str): this is the name (or part of the name) of the package to find.
        Returns:
            str: List of modules that can be imported with `import`/`using`
        """
        _, _, installed = await agent.context.get_jupyter_context()
        return str(list(filter(lambda module: name.lower() in module.lower(), installed)))

    @tool(autosummarize=True)
    async def search_package_registries(self, name: str, agent: AgentRef) -> str:
        """
        Search packages that can be installed using `Pkg.add` using a naive match (occursin)

        It might be worth checking installed packages first.

        E.g. Searching using the name "X" might return ["MimiX"] which is the name of the IAM
        
        you want to install

        Args:
            name (str): this is the name (or part of the name) of the package to find.

        Returns:
            str: List of modules that can be installed using Pkg.add
        """
        code = agent.context.get_code("search_packages", {"module": name})
        response = await agent.context.evaluate(
            code,
            parent_header={},
        )
        return str(response["return"])
    

    @tool(autosummarize=False)
    async def get_model_info(self, model_var_name: str, agent: AgentRef) -> dict:
        """
        Get information about Mimi model parameters and variables and which compartments they belong to.

        You should probably run this before asking the user for more information.

        Args:
            model_var_name (str): Variable name that contains the Mimi model in the REPL

        Returns:
            dict: Information about the Mimi Model  
        """
        code = agent.context.get_code("model_info", {"model": model_var_name})
        response = await agent.context.evaluate(
            code,
            parent_header={},
        )
        return response["return"]


    @tool(autosummarize=True)
    async def retrieve_documentation_for_module(self, package_name: str, agent: AgentRef) -> str:
        """
        Gets the specified module documentation

        Args:
            package_name (str): this is the name of the package to get information about.
        Returns:
            str: Markdown of the module docs
        """
        code = agent.context.get_code("get_module_docs", {"module": package_name})
        response = await agent.context.evaluate(
            code,
            parent_header={},
        )
        return response["return"]


    @tool(autosummarize=True)
    async def get_function_docstring(self, function_name: str, agent: AgentRef):
        """
        Use this tool to additional information on individual function such as their inputs, outputs and descrption (and generally anything else that would be in a docstring)
        
        Read the information returned to learn how to use the function and which arguments they take.
        
        The function names used in the input to this tool should include the entire module hierarchy

        If this fails, this means the function does not exist.
        
        Args:
            function_name (str): name of the function to lookup. 
        """
        code = f"""
            import DisplayAs, JSON3
            try {function_name} 
            catch 
                DisplayAs.unlimited(
                    JSON3.write(
                        Dict("docs" => "{function_name} not defined")
                    )
                )
            else
                docstring = string(@doc({function_name}))
                doc_object = Dict("docs" => docstring)
                DisplayAs.unlimited(
                    JSON3.write(doc_object)
                )
            end
        """
        response = await agent.context.beaker_kernel.evaluate(
            code,
            parent_header={},
        )
        docs = response["return"]["docs"]
        return docs

class Agent(NewBaseAgent):
    """
    You are assisting us in performing important scientific tasks.

    If you don't have the details necessary, you should use the ask_user tool to ask the user for them.
    """

    MODEL = "gpt-4o"
    

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        tools = [Toolset]
        super().__init__(context, tools, **kwargs)
        self.most_recent_user_query=''
        self.checked_code=False
        self.code_attempts=0
    
    def send_code(self, code: str, loop: LoopControllerRef) -> str:
        loop.set_state(loop.STOP_SUCCESS)
        preamble, code, coda = re.split("```\w*", code)
        result = json.dumps(
            {
                "action": "code_cell",
                "language": self.context.subkernel.KERNEL_NAME,
                "content": code.strip(),
            }
        )
        #check if successful then reset check code...
        return result
    
    #no_repl version
    @tool()
    async def submit_custom_code(self, code: str, agent: AgentRef, loop: LoopControllerRef) -> None:
        """
        Use this when you are ready to submit your custom code to the user. 
        
        Use other submit tools if you don't need to generate custom code.

        If there is a package is not yet installed, feel free to suggest a Pkg.add as well.
        
        Ensure to handle any required dependencies, and provide a well-documented and efficient solution. Feel free to create helper functions or classes if needed.
        
        Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
        You MUST wrap the code with a line containing three backticks before and after the generated code like the code below but replace the "triple_backticks":
        ```
        import DataFrames
        ```

        No additional text is needed in the response, just the code block with the triple backticks.

        Args:
            code (str): Julia code block to be submitted to the user inside triple backticks.
        """
        return self.send_code(code, loop)
    
    @tool()
    async def generate_plot_var_code(self, model_name: str, component_name: str, variable_name: str, agent: AgentRef, loop: LoopControllerRef) -> None: 
        """
        Generate the code `Mimi.plot(${model_name}, :${component_name}, :${variable_name})`.

        Once this code is generated, please give it to `submit_custom_code`

        All the information should be found if you run `get_model_info`.

        Args:
            model_name (str): Variable name of the Mimi model in the REPL
            component_name (str): The component of interest
            variable_name (str): The variable to plot INSIDE the component
        """
        code = f"Mimi.plot({model_name}, :{component_name}, :{variable_name})"
        return code

