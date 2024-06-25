import logging
import contextlib
from importlib import import_module
import io
import json
from typing import TYPE_CHECKING, Any, Dict
import pickle
import os

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.subkernels.python import PythonSubkernel
import pkgutil
from .agent import ChirhoAgent #to change dynamically on new context creation

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from .new_base_agent import NewBaseAgent
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

logger = logging.getLogger(__name__)

class ChirhoContext(BaseContext): #to change dynamically on new context creation
    slug = "bio" #to change dynamically on new context creation
    agent_cls: "NewBaseAgent" = ChirhoAgent

    def __init__(
        self,
        beaker_kernel: "LLMKernel",
        config: Dict[str, Any],
    ) -> None:
        self.functions = {}
        self.config = config
        self.variables={}
        self.imported_modules={}
        self.few_shot_examples=''
        self.code_blocks=[] #{'code':str,'execution_status':not_executed,executed_successfully,'execution_order':int,'output':output from running code block most recent time.}
        self.code_block_print='\n\n'.join([f'Code Block[{i}]: {self.code_blocks[i]["code"]}\nExecution Status:{self.code_blocks[i]["execution_status"]}\nExecution Order:{self.code_blocks[i]["execution_order"]}\nCode Block Output or Error:{self.code_blocks[i]["output"]}' for i in range(len(self.code_blocks))])
        self.context_conf = {
            "slug": "beaker_bio",
            "package": "beaker_bio_context.context",
            "class_name": "ChirhoContext",
            "library_names": ["chirho"],
            "task_description": "Causal Reasoning"
        }
        super().__init__(beaker_kernel, self.agent_cls, config)
        if not isinstance(self.subkernel, PythonSubkernel):
            raise ValueError("This context is only valid for Python.")
        
    async def get_jupyter_context(self):
        imported_modules=[]
        variables={}
        code = self.agent.context.get_code("get_jupyter_variables")
        await self.agent.context.evaluate(
            code,
            parent_header={},
        )
        jupyter_context={'user_vars':{},'imported_modules':[]}
        try:
            jupyter_context=pickle.load(open('/tmp/jupyter_state.pkl', 'rb'))
        except:
            logger.error('failed to load jupyter_state.pkl')

        variables=jupyter_context['user_vars']
        imported_modules=jupyter_context['imported_modules']
        return variables,imported_modules
    
    async def post_execute(self, message):
        self.variables,self.imported_modules=await self.get_jupyter_context()
        self.agent.debug(event_type="update_code_env",content={
                    "variables": self.variables,
                })
        self.agent.debug(event_type="code",content={
                    "imported_modules": self.imported_modules,
                })
    
    async def auto_context(self):
        from .lib.utils import query_examples 
        most_recent_user_query=''
        for message in self.agent.messages:
            if message['role']=='user':
                most_recent_user_query=message['content']
        if most_recent_user_query!=self.agent.most_recent_user_query:
            self.few_shot_examples=query_examples(most_recent_user_query)
            self.agent.debug(event_type="few_shot_examples",content={
                        "few_shot_examples": self.few_shot_examples,
                        "user_query":most_recent_user_query
                    })
        
        intro=f"""You are an exceptionally intelligent coding assistant that consistently delivers accurate and reliable responses to user instructions.
ChiRho is a causal extension to the Pyro probabilistic programming language. It was built to bridge the gap between the capabilities of modern probabilistic programming systems, such as Pyro, and the needs of policymakers, scientists, and AI researchers, who often want to use models to answer their questions about cause-and-effect relationships. 
As a non-exhaustive set of examples, ChiRho makes it easier to answer the following kinds of causal questions that appear frequently in practice.

Interventional: How many COVID-19 hospitalizations will occur if the USA imposes a national mask mandate?
Counterfactual: Given that 100,000 people were infected with COVID-19 in the past month, how many would have been infected if a mask mandate had been in place?
Explanation: Why were 100,000 people infected with COVID-19 in the past month?
Causal structure discovery: What individual attributes influence risk of COVID-19 hospitalization?

You should ALWAYS try looking up the what the user is asking you to do or portions of what the user is asking you to do in the documentation to get a sense of how it can be done.
You should ALWAYS think about which functions and classes from chirho you are going to use before you write code. Try to use chirho as much as possible.
You can do so in the following ways: 
If the functions you want to use are in the context below, no need to look them up again.
Otherwise, first try to use the ChirhoToolset.search_functions_classes to search for relevant functions and classes.
If that does not provide enough information, lookup the available functions for related modules using ChirhoToolset.get_available_functions.
If there is a main class or function you are using, you can lookup all the information on it and all the objects and functions required to use it using ChirhoToolset.get_class_or_function_full_information.
Use this when you want to instantiate a complicated object.

You can lookup source code for individual functions or classes using the ChirhoToolset.get_functions_and_classes_source_code before using a function from chirho.

Below is some information on the submodules in chirho:

chirho.counterfactual - This module contains code for Effect handlers for counterfactual world splitting 
chirho.dynamical - This module contains code for Effect handlers for performing interventions
chirho.explainable - This module contains code for Effect handler utilities for computing probabilistic quantities for partially deterministic models which is useful for counterfactual reasoning
chirho.indexed - This module contains code for Effect handler utilities for named indices in ChiRho which is useful for manipluating and tracking counterfactual worlds
chirho.interventional - This module contains code for Operations and effect handlers for counterfactual reasoning in dynamical systems
chirho.observational - This module contains code for Operations and effect handlers for robust estimation
chirho.robust - This module contains code for Operations and effect handlers for causal explanation
        
Additionally here are some similar examples of similar user requests and your previous successful code generations in the format [[Request,Code]].
If the request from the user is similar enough to one of these examples, use it to help write code to answer the user's request.
    
{self.few_shot_examples}
""" #to change dynamically on new context creation

        code_environment=f"""These are the variables in the user's current code environment with key value pairs:
{self.variables}

The user has also imported the following modules: {','.join(self.imported_modules)}. So you don't need to import them when generating code.
When writing code that edits the variables that the user has in their environment be sure to modify them in place. 
For example if we have a variable a=1, if we wanted to change a to 2, we you write a=2.
When the user asks you to perform an action, if they specifically mention a variable name, be sure to use that variable.
Additionally if the object they ask you to update is similar to an object in the code environment, be sure to use that variable. 
"""
        outro = f"""
Please answer any user queries or perform user instructions to the best of your ability, but do not guess if you are not sure of an answer.
"""

        result = "\n".join([intro,code_environment,outro])
        return result
    
    async def retrieve_documentation(self):
        """
        Gets the specified libraries help documentation and stores it into a dictionary:
        {   
            "package_name": "help documentation",
            ....
        }
        """
        documentation = {}
        for package in self.context_conf.get('library_names', []):
            module = import_module(package)

            # Redirect the standard output to capture the help text
            with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                help(module)
                # Store the help text in the dictionary
                documentation[package] = buf.getvalue()
        print(f"Fetched help for {documentation.keys()}")
        return documentation
    
