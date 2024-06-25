import json
import logging
import re
from typing import Optional

import pandas

from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, is_tool, tool, toolset

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
from .CodeLATS.code_lats import use_lats
logger = logging.getLogger(__name__)
from archytas.tools import PythonTool
from .new_base_agent import NewBaseAgent
import importlib
import io
import sys
import contextlib
import traceback
import inspect
from pydantic import BaseModel
from typing import get_args, get_origin
from typing import Annotated,Union,List


@toolset()
class ChirhoToolset: #to change dynamically on new context creation
    """Toolset for Chirho context""" #to change dynamically on new context creation
#    @tool(autosummarize=True)
#    async def generate_code_using_lats(self, query: str, agent: AgentRef) -> None:
#        use_lats(query,model='gpt-3.5-turbo-1106',tree_depth=2)#'gpt-4-1106-preview''gpt-4-1106-preview'

    #generate_code.__doc__

    @tool(autosummarize=True)
    async def get_available_functions(self, package_name: str, agent: AgentRef):
        """
        Querying against the module or package should list all available submodules and functions that exist, so you can use this to discover available
        functions and the query the function to get usage information.
        You should ALWAYS try to run this on specific submodules, not entire libraries. For example, instead of running this on `chirho` you should
        run this function on `chirho.interventional`. In fact, there should almost always be a `.` in the `package_name` argument.
        
        This function should be used to discover the available functions in the target library or module and get an object containing their docstrings so you can figure out how to use them.

        This function will return an object and store it into self.__functions. The object will be a dictionary with the following structure:
        {
            function_name: <function docstring>,
            ...
        }

        Read the docstrings to learn how to use the functions and which arguments they take.

        Args:
            package_name (str): this is the name of the package to get information about. For example "chirho.counterfactual"   
        """
        functions = {}
        code = agent.context.get_code("info", {"package_name": package_name})
        info_response = await agent.context.evaluate(
            code,
            parent_header={},
        )
        with open('/tmp/info.json', 'r') as f:
            info = json.loads(f.read())        
        for var_name, info in info.items():
            if var_name in functions:
                functions[var_name] = info
            else:
                functions[var_name] = info

        agent.context.functions.update(functions)

        return functions

    
    @tool(autosummarize=True)
    async def get_functions_and_classes_docstring(self, list_of_function_or_class_names: list, agent: AgentRef):
        """
        Use this tool to additional information on individual function or class such as their inputs, outputs and description (and generally anything else that would be in a docstring)
        You should ALWAYS use this tool before writing or checking code to check the function signatures of the functions or classes you are about to use.
        
        Read the information returned to learn how to use the function or class and which arguments they take.
        
        The function and class names used in the input to this tool should include the entire module hierarchy, ie. chirho.modeling.triples.Triple
        
        Args:
            list_of_function_or_class_names (list): this is a list of the the names of the functions and/or classes to get information about. For example ["chirho.modeling.triples.Triple","chirho.explainable.handlers.explanation.SplitSubsets"]   
        """
        #to change dynamically on new context creation
        #TODO: figure out cause of this and remove ugly filter
        if type(list_of_function_or_class_names)==dict:
            list_of_function_or_class_names=list_of_function_or_class_names['list_of_function_or_class_names']
        help_string=''
        print(list_of_function_or_class_names)
        for func_or_class_name in list_of_function_or_class_names:
            module_name=func_or_class_name.rsplit('.', 1)[0]
            importlib.import_module(module_name)
    
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                help(func_or_class_name)
                # Store the help text in the dictionary
                help_text = buf.getvalue()
            help_string+=f'{func_or_class_name}: {help_text}'
            agent.context.functions[func_or_class_name]=help_text
        return help_string
    
    @tool(autosummarize=True)
    async def get_functions_and_classes_source_code(self, list_of_function_or_class_names: list, agent: AgentRef):
        """
        Use this tool to additional information on individual function or class such as their inputs, outputs and description (and generally anything else that would be in a docstring)
        You should ALWAYS use this tool before writing or checking code to check the function signatures of the functions or classes you are about to use.
        
        Read the information returned to learn how to use the function or class and which arguments they take.
        
        The function and class names used in the input to this tool should include the entire module hierarchy, ie. chirho.counterfactual.internals.site_is_ambiguous
        
        Args:
            list_of_function_or_class_names (list): this is a list of the the names of the functions and/or classes to get information about. For example ["chirho.modeling.triples.Triple","chirho.explainable.handlers.explanation.SplitSubsets"]     
        """
        #to change dynamically on new context creation
        #TODO: figure out cause of this and remove ugly filter
        if type(list_of_function_or_class_names)==dict:
            list_of_function_or_class_names=list_of_function_or_class_names['list_of_function_or_class_names']
        help_string=''
        for func_or_class_name in list_of_function_or_class_names:
            module_path, object_name = func_or_class_name.rsplit('.', 1)
            module=importlib.import_module(module_path)
            obj = getattr(module, object_name)
            try:
                source_code=inspect.getsource(obj)
            except TypeError:
                source_code=inspect.getsource(module)
            #TODO: maybe use help on the object if it is an object and not a class?
            help_string+=f'{func_or_class_name} source code: \n{source_code}'
            #agent.context.functions[func_or_class_name]=help_text
        return help_string
    
    @tool(autosummarize=True)
    async def search_documentation(self, query: str):
        """
        Use this tool to search the documentation for sections relevant to the task you are trying to perform.
        Input should be a natural language query meant to find information in the documentation as if you were searching on a search bar.
        Response will be sections of the documentation that are relevant to your query.
        
        Args:
            query (str): Natural language query. Some Examples - "ode model", "sir model", "using dkg package" 
        """
        #to change dynamically on new context creation
        from .lib.utils import query_docs
        return query_docs(query)
    
    @tool(autosummarize=True)
    async def search_functions_classes(self, query: str):
        """
        Use this tool to search the code in the chirho repo for function and classes relevant to your query.
        Input should be a natural language query meant to find information in the documentation as if you were searching on a search bar.
        Response will be a string with the top few results, each result will have the function or class doc string and the source code (which includes the function signature)
        
        Args:
            query (str): Natural language query. Some Examples - "ode model", "sir model", "using dkg package"
        """
        #to change dynamically on new context creation
        from .lib.utils import query_functions_classes
        return query_functions_classes(query)


class ChirhoAgent(NewBaseAgent):
    """
    You are assisting us in performing important scientific tasks.

    If you don't have the details necessary, you should use the ask_user tool to ask the user for them.
    """

    def __init__(self, context: BaseContext = None, tools: list = None, **kwargs):
        tools = [ChirhoToolset]
        super().__init__(context, tools, **kwargs)
        self.context_conf = {
            "slug": "beaker_bio",
            "package": "beaker_bio_context.context",
            "class_name": "ChirhoContext",
            "library_names": ["chirho"],
            "task_description": "Causal Reasoning"
            }
        self.most_recent_user_query=''
        self.checked_code=False
        self.code_attempts=0
            
    @tool()
    async def submit_code(self, code: str, agent: AgentRef, loop: LoopControllerRef) -> None:
        """
        Use this when you are ready to submit your code to the user.
        
        
        Ensure to handle any required dependencies, and provide a well-documented and efficient solution. Feel free to create helper functions or classes if needed.
        
        Please generate the code as if you were programming inside a Jupyter Notebook and the code is to be executed inside a cell.
        You MUST wrap the code with a line containing three backticks before and after the generated code like the code below but replace the 'triple_backticks':
        ```
        import chirho
        ```

        No additional text is needed in the response, just the code block with the triple backticks.
        

        Args:
            code (str): python code block to be submitted to the user inside triple backticks.
        """
        loop.set_state(loop.STOP_SUCCESS)
        preamble, code, coda = re.split("```\w*", code)
        result = json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
        #check if successful then reset check code...
        return result

