import requests; import pandas as pd; import numpy as np; import scipy;
import json; import mira;
import sympy; import itertools; from mira.metamodel import *; from mira.modeling import Model;
from mira.sources.amr import model_from_json; from mira.modeling.viz import GraphicalModel;
from mira.modeling.amr.stockflow import template_model_to_stockflow_json;
from mira.modeling.amr.regnet import template_model_to_regnet_json;