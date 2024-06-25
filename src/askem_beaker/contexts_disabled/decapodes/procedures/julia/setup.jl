using ACSets
using Catlab, Catlab.Graphics
using CombinatorialSpaces
using Decapodes
using DiagrammaticEquations
using DiagrammaticEquations.Deca
using ImageIO, ImageShow

_model_reset_cache = Dict()
decapode = @decapode begin end
