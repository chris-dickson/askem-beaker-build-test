{{ var_name|default("decapode") }} = (haskey(_model_reset_cache, :{{ var_name|default("decapode") }}) ? _model_reset_cache[:{{ var_name|default("decapode") }}] : @decapode begin end)
