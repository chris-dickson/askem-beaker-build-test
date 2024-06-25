import DisplayAs
using Catlab
using JSON3

_preview = Dict()
_var_syms = names(Main)

for _var_sym in _var_syms
    _var = eval(_var_sym)
    if typeof(_var) <: ACSet
        _graph = Catlab.Graphics.to_graphviz_property_graph(_var)
        _html = IOBuffer()
        _text = IOBuffer()

        show(_html, "text/html", _var)
        show(_text, "text/plain", _var)

        _preview["$(_var_sym)"] = Dict(
            "application/x-askem-decapode-json-graph" => _graph,
            "application/json" => _graph,
            "text/html" => String(take!(_html)),
            "text/plain" => String(take!(_text)),
        )
    end
end

_preview |> DisplayAs.unlimited ∘ JSON3.write
