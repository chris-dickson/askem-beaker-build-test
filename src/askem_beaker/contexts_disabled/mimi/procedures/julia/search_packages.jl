import Pkg.Registry as _Registry
import JSON3, DisplayAs


_SEARCH_STRING = "{{ module }}"

_MATCHES = []
for registry in _Registry.reachable_registries()
    for package in values(registry.pkgs)
        if occursin(_SEARCH_STRING, package.name)
            push!(_MATCHES, package.name)
        end
    end
end

_MATCHES |> DisplayAs.unlimited ∘ JSON3.write
