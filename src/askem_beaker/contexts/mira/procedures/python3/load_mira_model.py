import copy
from mira.sources.amr import model_from_json
amr_json = {{amr_json}}
{{ var_name|default("model") }} = model_from_json(amr_json)
_{{ var_name|default("model") }}_orig = copy.deepcopy({{ var_name|default("model") }})