import JSON3, DisplayAs
_IGNORED_SYMBOLS = [:Base, :Core, :InteractiveUtils, :Main]

_from_module = {{from_module | default("true") }}
_return_source = {{ return_source | default("false") }} # TODO: Use this with CodeTracking.jl
_selected_module = :{{ module | default("nothing") }}
_chosen_funcs_str = "{{ function_names | default("") }}"


_function_names = 
    if _from_module
        _module_names = 
            if !isnothing(_selected_module)
                filter(x -> in(x, _IGNORED_SYMBOLS) && isa(x, Module), names(Main))
            else
                [_selected_module]
            end
        filter(!in(_module_names), reduce(vcat, [names(eval(mod); all=true) for mod in _module_names]; init=[]))
    else
        Symbol.(split(_chosen_funcs_str, ","))
    end

_docs = Dict{Symbol, Any}()
for func in _function_names
    _docs[func] = string(eval(:(@doc $func)))
end

_docs |> DisplayAs.unlimited ∘ JSON3.write
