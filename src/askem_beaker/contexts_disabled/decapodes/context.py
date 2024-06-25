import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict

import requests

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import action

from .agent import DecapodesAgent
from askem_beaker.utils import get_auth
from beaker_kernel.lib.subkernels.julia import JuliaSubkernel

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.subkernels.base import BaseSubkernel


logger = logging.getLogger(__name__)



class DecapodesContext(BaseContext):

    agent_cls = DecapodesAgent

    def __init__(self, beaker_kernel: "LLMKernel", config: Dict[str, Any]) -> None:
        self.target = "decapode"
        self.auth = get_auth()
        self.reset()
        super().__init__(beaker_kernel, self.agent_cls, config)
        if not isinstance(self.subkernel, JuliaSubkernel):
            raise ValueError("This context is only valid for Julia.")
        


    async def setup(self, context_info, parent_header):
        self.config["context_info"] = context_info

        def fetch_model(model_id):
            meta_url = f"{os.environ['HMI_SERVER_URL']}/models/{model_id}"
            response = requests.get(meta_url, auth=self.auth.requests_auth())
            if response.status_code >= 300:
                raise Exception(f"Failed to retrieve model {model_id} from server returning {response.status_code}")
            model = json.dumps(response.json()["model"])
            return model

        variables = {
            var_name: fetch_model(decapode_id) for var_name, decapode_id in context_info.items()
        }

        command = "\n".join(
            [
                self.get_code("setup"),
                self.get_code("load_model", {
                    "variables": variables,
                }),
            ]
        )
        print(f"Running command:\n-------\n{command}\n---------")
        await self.execute(command)
        print("Decapodes creation environment set up")


    async def post_execute(self, message):
        await self.send_decapodes_preview_message(parent_header=message.parent_header)

    def reset(self):
        pass

    async def generate_preview(self):
        preview = await self.evaluate(self.get_code("generate_preview", {"target": self.target}))
        content = preview["return"]

        result = {
            "decapodes": content,
        }
        return result

    async def auto_context(self):
        return """You are an scientific modeler whose goal is to construct a DecaExpr for Decapodes.jl modeling library.

Explanation of Decapodes.jl from the docs
> Discrete Exterior Calculus Applied to Partial and Ordinary Differential Equations (Decapodes) is a diagrammatic language
> used to express systems of ordinary and partial differential equations. The Decapode provides a visual framework for
> understanding the coupling between variables within a PDE or ODE system, and a combinatorial data structure for working
> with them. Below, we provide a high-level overview of how Decapodes can be generated and interpreted.

However, we will just be instantiating a model with SyntacticModels.jl
Explanation of SyntacticModels from the docs.
> SyntacticModels.jl is a Julia library for representing models as syntactic expressions.
> The driving example for this library is the need to interoperate models between programming languages in the DARPA
> ASKEM Program. The AlgebraicJulia ecosystem includes some great tools for specifying modeling languages, but they are
> deeply connected to the Julia language. This package aims to provide simple tools for specifying domain specific
> programming languages that can be used to exchange the specification of scientific models between host languages.
> We heavily use the MLStyle.jl package for defining Algebraic Data Types so you should familiarize yourself with those
> concepts before reading on in this documentation.
>
> The easiest way to write down a DecaExpr is in our DSL and calling the parser.
```
_expr = Decapodes.parse_decapode(quote
  X::Form0{Point}
  V::Form0{Point}

  k::Constant{Point}

  ∂ₜ(X) == V
  ∂ₜ(V) == -1*k*(X)
end
)
```


The definition of the current model is:
--- START ---
{self.decapodes_expression_dsl}
--- END ---

Currently, the model has the following structure:
--- START ---
""" + await self.model_structure() + """
--- END ---

Please answer any user queries to the best of your ability, but do not guess if you are not sure of an answer.
If you are asked to manipulate, stratify, or visualize the model, use the generate_code tool.
"""

    async def model_structure(self) -> str:
        """
        Inspect the model and return information and metadata about it.

        This should be used to answer questions about the model.


        Returns:
            str: a JSON representation of the model
        """
        # Update the local dataframe to match what's in the shell.
        # This will be factored out when we switch around to allow using multiple runtimes.
        amr = (
            await self.evaluate(
                f"_expr |> string"
            )
        )["return"]
        return json.dumps(amr, indent=2)

    async def send_decapodes_preview_message(
        self, server=None, target_stream=None, data=None, parent_header=None
    ):
        if parent_header is None:
            parent_header = {}
        preview = await self.evaluate(self.get_code("expr_to_info", {"target": self.target}))
        content = preview["return"]
        if content is None:
            raise RuntimeError("Info not returned for preview")

        self.beaker_kernel.send_response(
            "iopub", "decapodes_preview", content, parent_header=parent_header
        )

    @action()
    async def compile_expr(self, message):
        """
        Compiles a string declaration of the Decapodes Domain Specific Langauge to a SummationDecapode object.
        The contents of the "declaration" element should match what would be put in a  `@decapode` macro block.
        See https://algebraicjulia.github.io/Decapodes.jl/stable/klausmeier/#Model-Representation
        """
        content = message.content

        declaration = content.get("declaration")
        self.decapodes_expression_dsl = declaration

        command = "\n".join(
            [
                self.get_code("construct_expr", {"declaration": declaration, "target": self.target}),
                "nothing"
            ]
        )
        await self.execute(command)

        self.beaker_kernel.send_response(
            "iopub", "compile_expr_response", {"successs": True}, parent_header=message.header
        )
        await self.send_decapodes_preview_message(parent_header=message.header)
    compile_expr._default_payload = """{
  "declaration": "h::Form0\\n  Γ::Form1\\n  n::Constant\\n\\n  ḣ == ∂ₜ(h)\\n  ḣ == ∘(⋆, d, ⋆)(Γ * d(h) * avg₀₁(mag(♯(d(h)))^(n-1)) * avg₀₁(h^(n+2)))"
}"""


    @action()
    async def construct_amr(self, message):
        """
        Constructs an AMR and returns it as a `construct_amr_response` message.
        """
        content = message.content

        header =  {
            "description": content.get("description", None),
            "name": content.get("name", None),
            "_type": "Header",
            "model_version": "v1.0",
            "schema": "https://raw.githubusercontent.com/DARPA-ASKEM/Model-Representations/decapodes-intertypes/decapodes/decapodes_schema.json",
            "schema_name": "decapode"
        }
        id_value = content.get("id", None)
        if id_value:
            header['id'] = id_value

        preview = await self.evaluate(self.get_code("expr_to_info", {"target": self.target}))
        model = preview["return"]["application/json"]

        amr = {
            "header": header,
            "model": model,
            "_type": "ASKEMDecaExpr",
            "annotations": [],
        }

        self.beaker_kernel.send_response(
            "iopub", "construct_amr_response", amr, parent_header=message.header
        )
    construct_amr._default_payload = """{
  "id": "(Optional)model_id",
  "name": "model_name",
  "description": "model description"
}"""

    @action()
    async def save_amr(self, message):
        """
        Saves your decapode to the HMI server.
        """
        content = message.content

        header = content["header"]
        header["_type"] = "Header"

        preview = await self.evaluate(self.get_code("expr_to_info", {"target": self.target}))
        model = preview["return"]["application/json"]

        amr = {
            "header": header,
            "model": model,
            "_type": "ASKEMDecaExpr",
            "annotations": [],
        }

        create_req = requests.post(
            f"{os.environ['HMI_SERVER_URL']}/models", json=amr,
            auth=self.auth.requests_auth()
        )
        new_model_id = create_req.json()["id"]
        logger.debug(f"Created model {new_model_id}")

        self.beaker_kernel.send_response(
            "iopub", "save_model_response", content, parent_header=message.header
        )
    save_amr._default_payload = """{
  "header": {
    "id": "(Optional)model_id",
    "name": "model_name",
    "description": "model description"
  }
}"""

    @action()
    async def model_to_equation(self, message):
        """
        Converts a decapode model/expression to an equation.
        The equation is returned in the content of the `model_to_equation_response` message.
        """
        content = message.content
        model_name = content.get("model_name", self.target)

        equation_code = self.get_code("model_to_equation", {
            "var_name": model_name,
        })
        equationStr = (await self.evaluate(equation_code))["return"]

        content = {
            "success": True,
            "equation": equationStr
        }
        self.beaker_kernel.send_response(
            "iopub", "model_to_equation_response", content, parent_header=message.header
        )
    model_to_equation._default_payload = """{
  "model_name": "(optional - default: decapode) variable_name_of_model"
}"""


    @action(action_name="reset")
    async def reset_action(self, message):
        """
        Resets the a model as if it were freshly spawned, undoing any changes.
        """
        content = message.content

        model_name = content.get("model_name", self.target)
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
        await self.send_decapodes_preview_message(parent_header=message.header)
    reset_action._default_payload = """{
  "var_name": "(optional - default: decapode) variable_name_of_model"
}"""

    @action()
    async def save_solution(self, message):
        """
        Saves a solution to the HMI server.
        """
        content = message.content

        name = content.get("name")
        description = content.get("description", "")
        filename = content.get("filename", None)
        soln_name = content.get("soln_name", "soln")
        dataservice_url = os.environ["HMI_SERVER_URL"]

        if filename is None:
            filename = "dataset.csv"

        new_dataset = {}
        new_dataset["name"] = name
        new_dataset["description"] = description
        new_dataset["fileNames"] = [filename]
        new_dataset["temporary"] = False

        import pprint
        logger.debug(f"Creating dataset {pprint.pformat(new_dataset)}")
        create_req = requests.post(f"{dataservice_url}/datasets", auth=self.auth.requests_auth(), json=new_dataset)
        new_dataset_id = create_req.json()["id"]

        new_dataset["id"] = new_dataset_id
        logger.debug(f"Dataset created: {new_dataset_id}")

        logger.debug(f"Uploading {filename} to {new_dataset_id}")
        new_dataset_url = f"{dataservice_url}/datasets/{new_dataset_id}"
        data_url_req = requests.get(f"{new_dataset_url}/upload-url?filename={filename}", auth=self.auth.requests_auth())
        data_url = data_url_req.json().get('url', None)
        logger.debug(f"`{filename}` uploaded")

        code = self.get_code(
            "save_sol",
            {
                "soln_name": soln_name,
                "data_url": data_url,
            }
        )
        df_response = await self.execute(code)

        if df_response:
            self.beaker_kernel.send_response(
                "iopub",
                "save_solution_response",
                {
                    "dataset_id": new_dataset_id,
                    "filename": filename,
                },
            )
    save_solution._default_payload = """{
  "name": "new_model_id",
  "description": "new model description",
  "filename": "(optional - default: dataset.csv) name_of_file",
  "soln_name": "solution name"
}"""
