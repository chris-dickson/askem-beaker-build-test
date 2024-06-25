import DisplayAs

input = {{ var_name|default("decapode") }}
contractedDeca = contract_operators(input)

# decaExpr = Term(input);
decaExpr = Term(contractedDeca);
output = sprint((io, x) -> DiagrammaticEquations.pprint(io, x), decaExpr) 
output |> DisplayAs.unlimited
