import json
import logging
import re

import requests
from archytas.react import Undefined
from archytas.tool_utils import AgentRef, LoopControllerRef, tool

from beaker_kernel.lib.agent import BaseAgent
from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.jupyter_kernel_proxy import JupyterMessage
from typing import Collection, Iterable, Optional, Tuple

logging.disable(logging.WARNING)  # Disable warnings
logger = logging.Logger(__name__)


class MiraModelEditAgent(BaseAgent):
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
    async def replace_template_name(self, old_name: str, new_name: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to rename a template that is part of a model.

        Args:
            old_name (str): The old/existing name of the template as it exists in the model before changing.
            new_name (str): The name that the template should be changed to.
        """
        code = agent.context.get_code("replace_template_name", {"old_name": old_name, "new_name": new_name})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def remove_template(self, template_name: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to remove an existing template that is part of a model.

        Args:
            template_name (str): This is the name of the template that is to be removed.
        """
        code = agent.context.get_code("remove_template", {"template_name": template_name })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )


    @tool()
    async def replace_state_name(self, template_name: str, old_name: str, new_name: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to rename a state name within a template that is part of a model.

        Args:
            template_name (str): the template within the model where these changes will be made
            old_name (str): The old/existing name of the state as it exists in the model before changing.
            new_name (str): The name that the state should be changed to.
        """
        code = agent.context.get_code("replace_state_name", {"template_name": template_name, "old_name": old_name, "new_name": new_name})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
  
    @tool()
    async def add_observable(self, new_id: str, new_name: str, new_expression: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add an observable.

        Args:
            new_id (str): The new ID provided for the observable. If this is not provided the value for new_name should be used
            new_name (str): The new name provided for the observable. If this is not provided for the new_id should be used.
            new_expression (str): The expression that the observable represents.
        """
        code = agent.context.get_code("add_observable", {"new_id": new_id, "new_name": new_name, "new_expression": new_expression})
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
  
    @tool()
    async def remove_observable(self, remove_id: str, agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to remove an observable.

        Args:
            remove_id (str): The existing observable id to be removed.
        """
        code = agent.context.get_code("remove_observable", {"remove_id": remove_id })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps(
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_natural_conversion_template(self,
        subject_name: str, 
        subject_initial_value: float,
        outcome_name: str, 
        outcome_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural conversion to the model. 
        A natural conversion is a template that contains two states and a transition where one state is sending population to the transition and one state is recieving population from the transition.
        The transition rate may only depend on the subject state.
        
        An example of this would be "Add a new transition from S to R with the name vaccine with the rate of v" 
        Where S is the subject state, R is the outcome state, vaccine is the template_name, and v is the template_expression.

        Args:
            subject_name (str): The state name that is the source of the new transition. This is the state population comes from.
            subject_initial_value (float): The number assosiated with the subject state at its first step in time. If not known or not specified the default value of `1` should be used.
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter. 
            parameter_units (str): The units assosiated with the parameter. 
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """
        
        code = agent.context.get_code("add_natural_conversion_template", {
            "subject_name": subject_name, 
            "subject_initial_value": subject_initial_value,
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_controlled_conversion_template(self,
        subject_name: str, 
        subject_initial_value: float,
        outcome_name: str, 
        outcome_initial_value: float,
        controller_name: str,
        controller_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled conversion to the model. 
        A controlled conversion is a template that contains two states and a transition where one state is sending population to the transition and one state is recieving population from the transition.
        This transition rate depends on a controller state. This controller state can be an existing or new state in the model.
        
        An example of this would be "Add a new transition from S to R with the name vaccine with the rate of v. v depends on I"
        Where S is the subject state, R is the outcome state, vaccine is the template_name, and v is the template_expression and I is the controller_name. 

        Args:
            subject_name (str): The state name that is the source of the new transition. This is the state population comes from.
            subject_initial_value (float): The number assosiated with the subject state at its first step in time. If not known or not specified the default value of `1` should be used.
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_controlled_conversion_template", {
            "subject_name": subject_name, 
            "subject_initial_value": subject_initial_value,
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "controller_name": controller_name,
            "controller_initial_value": controller_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_natural_production_template(self,
        outcome_name: str, 
        outcome_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural production to the model. 
        A natural production is a template that contains one state which is recieving population by one transition. The transition will not depend on any state.

        An example of this would be "Add a new transition from the transition rec to S with a rate of f."
        Where S is the outcome state, rec is the template_name, and f is the template_expression

        Args:
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_natural_production_template", {
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_controlled_production_template(self,
        outcome_name: str, 
        outcome_initial_value: float,
        controller_name: str,
        controller_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled production to the model. 
        A controlled production is a template that contains one state which is recieving population by one transition. This transition rate depends on a controller state. This controller state can be an existing or new state in the model.

        An example of this would be "Add a new transition from the transition rec to S with a rate of f. f depends on R. "
        Where S is the outcome state, rec is the template_name, f is the template_expression and the controller is R.

        Args:
            outcome_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            outcome_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_controlled_production_template", {
            "outcome_name": outcome_name,
            "outcome_initial_value": outcome_initial_value,
            "controller_name": controller_name,
            "controller_initial_value": controller_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_natural_degradation_template(self,
        subject_name: str, 
        subject_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a natural degradation to the model. 
        A natural degradation is a template that contains one state in which the population is leaving through one transition. The transition may only depend on the subject state.

        An example of this would be "Add a new transition from state S to transition rec with a rate of v."
        Where S is the subject state, rec is the template_name, and v is the template_expression.

        Args:
            subject_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            subject_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_natural_degradation_template", {
            "subject_name": subject_name,
            "subject_initial_value": subject_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def add_controlled_degradation_template(self,
        subject_name: str, 
        subject_initial_value: float,
        controller_name: str,
        controller_initial_value: float,
        parameter_name: str,
        parameter_units: str,
        parameter_value: float,
        parameter_description: str,
        template_expression: str,
        template_name: str,
        agent: AgentRef, loop: LoopControllerRef):
        """
        This tool is used when a user wants to add a controlled degradation to the model. 
        A controlled degradation is a template that contains one state in which the population is leaving through one transition. This transition rate depends on a controller state. This controller state can be an existing or new state in the model.

        An example of this would be "Add a new transition from S to rec with a rate of v. v depends on R."
        Where S is the subject state, rec is the template_name, v is the template_expression and R is the controller state.

        Args:
            subject_name (str): the state name that is the new transition's outputs. This is the state population moves to.
            subject_initial_value (float): The number assosiated with the output state at its first step in time. If not known or not specified the default value of `1` should be used.
            controller_name (str): The name of the controller state. This is the state that will impact the transition's rate.
            controller_initial_value (float): The initial value of the controller.
            parameter_name (str): the name of the parameter.
            parameter_units (str): The units assosiated with the parameter.
            parameter_value (float): This is a numeric value provided by the user. If not known or not specified the default value of `1` should be used.
            parameter_description (str): The description assosiated with the parameter. If not known or not specified the default value of `` should be used
            template_expression (str): The mathematical rate law for the transition.
            template_name (str): the name of the transition.
        """

        code = agent.context.get_code("add_controlled_degradation_template", {
            "subject_name": subject_name,
            "subject_initial_value": subject_initial_value,
            "controller_name": controller_name,
            "controller_initial_value": controller_initial_value,
            "parameter_name": parameter_name,
            "parameter_units": parameter_units,
            "parameter_value": parameter_value,
            "parameter_description": parameter_description,
            "template_expression": template_expression,
            "template_name": template_name  
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def replace_ratelaw(self,
        template_name: str,
        new_rate_law: str,
        agent: AgentRef, loop: LoopControllerRef
    ):
        """
        This tool is used when a user wants to replace a ratelaw.

        An example of this would be "change rate law of inf to S * I * z"
        Where inf is the template_name and "S * I * z" is the new_rate_law

        Args:
            template_name (str): This is the name of the template that has the rate law.
            new_rate_law (str): This is the mathematical expression used to determine the rate law.
        """
        code = agent.context.get_code("replace_ratelaw", {
            "template_name": template_name,
            "new_rate_law": new_rate_law
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )

    @tool()
    async def stratify(self,
        agent: AgentRef, loop: LoopControllerRef,
        key: str,
        strata: Collection[str],
        structure: Optional[Iterable[Tuple[str, str]]] = None,
        directed: bool = False,
        cartesian_control: bool = False,
        modify_names: bool = True
    ):
        """
        This tool is used when a user wants to stratify a model. 
        This will multiple the model utilizing several strata.

        An example of this would be "Stratify by location Toronto, Ottawa and Montreal. There are no interactions between members unless they are in the same location."
        Here we can see that the key is location.
        We can also see that the strata groups are Toronto, Ottawa and Montreal so we will write this as ["Toronto", "Ottawa", "Montreal"].
        The last sentence here informs us that cartesian_control is True, directed is False, and structure can be left as []

        Args:
            key (str):
                The (singular) name which describe the stratification. Some examples include, ``"City"``, ``"Age"``, ``"Vacination_Status"``, and ``"Location"``
                If a key cannot be explicitly grabbed from try your best to categorize the strata  
            strata (Collection):
                These will be the individual groups used to stratify by. This should be converted to a list of strings for e.g., ``["boston", "nyc"]``
                or ``["geonames:4930956", "geonames:5128581"]``.
            structure (Optional):
                This describes how different strata within the same state are able to interact.
                An iterable of pairs corresponding to a directed network structure
                where each of the pairs has two strata. If none given, will assume a complete
                network structure. If no structure is necessary, pass an empty list. 
                By default this should be an empty list. 
            directed (bool):
                If the structure tuples are combinations this should be True. If they are permutations this should be false.
                If this value cannot be found it should default to False
            cartesian_control (bool):
                True if the strata from different state variables can interact. 
                For example Susceptible young people can interact with infected old poeple.
                false if they cannot interact.
                For example the infected people in Toronto do not interact with the susceptible people in Boston
                
                This will split all control relationships based on the stratification.

                This should be true for an SIR epidemiology model, the susceptibility to
                infected transition is controlled by infected. If the model is stratified by
                vaccinated and unvaccinated, then the transition from vaccinated
                susceptible population to vaccinated infected populations should be
                controlled by both infected vaccinated and infected unvaccinated
                populations.

                This should be false for stratification of an SIR epidemiology model based
                on cities, since the infected population in one city won't (directly,
                through the perspective of the model) affect the infection of susceptible
                population in another city.

                If this cannot be found it should default to False
            modify_names (bool):
                If true, will modify the names of the concepts to include the strata
                (e.g., ``"S"`` becomes ``"S_boston"``). If false, will keep the original
                names.
                If this cannot be found it should default to True
        """

        code = agent.context.get_code("stratify", {
            "key": key,
            "strata": strata,
            "structure": structure,
            "directed": directed,
            "cartesian_control": cartesian_control,
            "modify_names": modify_names
        })
        loop.set_state(loop.STOP_SUCCESS)
        return json.dumps( 
            {
                "action": "code_cell",
                "language": "python3",
                "content": code.strip(),
            }
        )
