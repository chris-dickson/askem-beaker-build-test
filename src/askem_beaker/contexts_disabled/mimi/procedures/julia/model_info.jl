import DisplayAs, JSON3
using Mimi

_MODEL = {{ model }}

Mimi.menu_item_list(_MODEL) |> DisplayAs.unlimited ∘ JSON3.write