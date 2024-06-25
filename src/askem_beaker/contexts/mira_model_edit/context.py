import copy
import datetime
import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth

from beaker_kernel.lib.context import BaseContext
from beaker_kernel.lib.utils import intercept

from .agent import MiraModelEditAgent
from askem_beaker.utils import get_auth

if TYPE_CHECKING:
    from beaker_kernel.kernel import LLMKernel
    from beaker_kernel.lib.subkernels.base import BaseSubkernel

logger = logging.getLogger(__name__)


class MiraModelEditContext(BaseContext):

	agent_cls = MiraModelEditAgent

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
		logger.debug(f"performing setup...")
		self.context_info = context_info
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

	@intercept()
	async def replace_template_name_request(self, message):
		content = message.content

		old_name  = content.get("old_name")
		new_name = content.get("new_name")

		code = self.get_code("replace_template_name", {
			"old_name": old_name,
			"new_name": new_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "replace_template_name_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def replace_state_name_request(self, message):
		content = message.content

		template_name  = content.get("template_name")
		old_name  = content.get("old_name")
		new_name = content.get("new_name")

		code = self.get_code("replace_state_name", {
			"template_name": template_name,
			"old_name": old_name,
			"new_name": new_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "replace_state_name_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_natural_conversion_template_request(self, message):
		content = message.content

		subject_name  = content.get("subject_name")
		subject_initial_value = content.get("subject_initial_value")
		outcome_name  = content.get("outcome_name")
		outcome_initial_value = content.get("outcome_initial_value")
		parameter_name = content.get("parameter_name")
		parameter_value = content.get("parameter_value")
		parameter_units = content.get("parameter_units")
		parameter_description = content.get("parameter_description")
		template_expression = content.get("template_expression")
		template_name = content.get("template_name")

		code = self.get_code("add_natural_conversion_template", {
			"subject_name": subject_name,
			"subject_initial_value": subject_initial_value,
			"outcome_name": outcome_name,
			"outcome_initial_value": outcome_initial_value,
			"parameter_name": parameter_name,
			"parameter_value": parameter_value,
			"parameter_units": parameter_units,
			"parameter_description": parameter_description,
			"template_expression": template_expression,
			"template_name": template_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_natural_conversion_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_natural_production_template_request(self, message):
		content = message.content

		outcome_name  = content.get("outcome_name")
		outcome_initial_value = content.get("outcome_initial_value")
		parameter_name = content.get("parameter_name")
		parameter_value = content.get("parameter_value")
		parameter_units = content.get("parameter_units")
		parameter_description = content.get("parameter_description")
		template_expression = content.get("template_expression")
		template_name = content.get("template_name")

		code = self.get_code("add_natural_production_template", {
			"outcome_name": outcome_name,
			"outcome_initial_value": outcome_initial_value,
			"parameter_name": parameter_name,
			"parameter_value": parameter_value,
			"parameter_units": parameter_units,
			"parameter_description": parameter_description,
			"template_expression": template_expression,
			"template_name": template_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_natural_production_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_natural_degradation_template_request(self, message):
		content = message.content

		subject_name  = content.get("subject_name")
		subject_initial_value = content.get("subject_initial_value")
		parameter_name = content.get("parameter_name")
		parameter_value = content.get("parameter_value")
		parameter_units = content.get("parameter_units")
		parameter_description = content.get("parameter_description")
		template_expression = content.get("template_expression")
		template_name = content.get("template_name")

		code = self.get_code("add_natural_degradation_template", {
			"subject_name": subject_name,
			"subject_initial_value": subject_initial_value,
			"parameter_name": parameter_name,
			"parameter_value": parameter_value,
			"parameter_units": parameter_units,
			"parameter_description": parameter_description,
			"template_expression": template_expression,
			"template_name": template_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_natural_degradation_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_controlled_conversion_template_request(self, message):
		content = message.content

		subject_name  = content.get("subject_name")
		subject_initial_value = content.get("subject_initial_value")
		outcome_name  = content.get("outcome_name")
		outcome_initial_value = content.get("outcome_initial_value")
		controller_name = content.get("controller_name")
		controller_initial_value = content.get("controller_initial_value")
		parameter_name = content.get("parameter_name")
		parameter_value = content.get("parameter_value")
		parameter_units = content.get("parameter_units")
		parameter_description = content.get("parameter_description")
		template_expression = content.get("template_expression")
		template_name = content.get("template_name")

		code = self.get_code("add_controlled_conversion_template", {
			"subject_name": subject_name,
			"subject_initial_value": subject_initial_value,
			"outcome_name": outcome_name,
			"outcome_initial_value": outcome_initial_value,
			"controller_name": controller_name,
			"controller_initial_value": controller_initial_value,
			"parameter_name": parameter_name,
			"parameter_value": parameter_value,
			"parameter_units": parameter_units,
			"parameter_description": parameter_description,
			"template_expression": template_expression,
			"template_name": template_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_controlled_conversion_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_controlled_production_template_request(self, message):
		content = message.content

		outcome_name  = content.get("outcome_name")
		outcome_initial_value = content.get("outcome_initial_value")
		controller_name = content.get("controller_name")
		controller_initial_value = content.get("controller_initial_value")
		parameter_name = content.get("parameter_name")
		parameter_value = content.get("parameter_value")
		parameter_units = content.get("parameter_units")
		parameter_description = content.get("parameter_description")
		template_expression = content.get("template_expression")
		template_name = content.get("template_name")

		code = self.get_code("add_controlled_production_template", {
			"outcome_name": outcome_name,
			"outcome_initial_value": outcome_initial_value,
			"controller_name": controller_name,
			"controller_initial_value": controller_initial_value,
			"parameter_name": parameter_name,
			"parameter_value": parameter_value,
			"parameter_units": parameter_units,
			"parameter_description": parameter_description,
			"template_expression": template_expression,
			"template_name": template_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_controlled_production_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_controlled_degradation_template_request(self, message):
		content = message.content

		subject_name  = content.get("subject_name")
		subject_initial_value = content.get("subject_initial_value")
		controller_name = content.get("controller_name")
		controller_initial_value = content.get("controller_initial_value")
		parameter_name = content.get("parameter_name")
		parameter_value = content.get("parameter_value")
		parameter_units = content.get("parameter_units")
		parameter_description = content.get("parameter_description")
		template_expression = content.get("template_expression")
		template_name = content.get("template_name")

		code = self.get_code("add_controlled_degradation_template", {
			"subject_name": subject_name,
			"subject_initial_value": subject_initial_value,
			"controller_name": controller_name,
			"controller_initial_value": controller_initial_value,
			"parameter_name": parameter_name,
			"parameter_value": parameter_value,
			"parameter_units": parameter_units,
			"parameter_description": parameter_description,
			"template_expression": template_expression,
			"template_name": template_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_controlled_degradation_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def remove_template_request(self, message):
		content = message.content

		template_name = content.get("template_name")

		code = self.get_code("remove_template", {
			"template_name": template_name
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "remove_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_parameter_request(self, message):
		content = message.content

		parameter_id  = content.get("parameter_id")
		name  = content.get("name")
		description = content.get("description")
		value = content.get("value")
		distribution = content.get("distribution")
		units_mathml = content.get("units_mathml")

		code = self.get_code("add_parameter", {
			"parameter_id": parameter_id,
			"name": name,
			"description": description,
			"value": value,
			"distribution": distribution,
			"units_mathml": units_mathml
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_parameter_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def update_parameter_request(self, message):
		content = message.content

		updated_id  = content.get("updated_id")
		replacement_value  = content.get("replacement_value")

		code = self.get_code("update_parameter", {
			"updated_id": updated_id,
			"replacement_value": replacement_value
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "update_parameter_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def add_observable_template_request(self, message):
		content = message.content

		new_id  = content.get("new_id")
		new_name  = content.get("new_name")
		new_expression  = content.get("new_expression")

		code = self.get_code("add_observable", {
			"new_id": new_id,
			"new_name": new_name,
			"new_expression": new_expression
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "add_observable_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def remove_observable_template_request(self, message):
		content = message.content

		remove_id  = content.get("remove_id")

		code = self.get_code("remove_observable", {
			"remove_id": remove_id
		})
		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "remove_observable_template_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

	@intercept()
	async def replace_ratelaw_request(self, message):
		content = message.content

		template_name  = content.get("template_name")
		new_rate_law  = content.get("new_rate_law")
		
		code = self.get_code("replace_ratelaw", {
			"template_name": template_name,
			"new_rate_law": new_rate_law
		})

		result = await self.execute(code)
		content = {
			"success": True,
			"executed_code": result["parent"].content["code"],
		}

		self.beaker_kernel.send_response(
			"iopub", "replace_ratelaw_response", content, parent_header=message.header
		)
		await self.send_mira_preview_message(parent_header=message.header)

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

		key = content.get("key")
		strata = content.get("strata")
		concepts_to_stratify = content.get("concepts_to_stratify")
		params_to_stratify = content.get("params_to_stratify")
		cartesian_control = content.get("cartesian_control")
		structure = content.get("structure")

		stratify_code = self.get_code("stratify", {
		    "key": key,
		    "strata": strata,
		    "concepts_to_stratify": concepts_to_stratify,
		    "params_to_stratify": params_to_stratify,
		    "cartesian_control": cartesian_control,
		    "structure": structure
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
