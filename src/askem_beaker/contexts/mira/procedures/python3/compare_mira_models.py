import itertools

from IPython.display import Image, display
from mira.dkg.web_client import is_ontological_child_web
from mira.metamodel import TemplateModelDelta

# Define the refinement function
refinement_fun = is_ontological_child_web

# Specify which models to visualize pairwise
models = {{model_vars}}

for pair in itertools.combinations(models, 2):
    # Compare the pair of models by name
    delta = TemplateModelDelta(locals()[pair[0]], locals()[pair[1]], refinement_fun)
    # Visualize the comparison
    filename = f"comparison_{pair[0]}_{pair[1]}.png"
    delta.draw_graph(filename, args="-Grankdir=TB")
    # Display the comparison
    display(Image(filename=filename))
