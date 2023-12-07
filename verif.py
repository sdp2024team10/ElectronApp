#!/usr/bin/env python3
import sys
import json
import numpy as np
import sympy as sp
from sympy.parsing.latex import parse_latex
# from enforce_typing import enforce_types
import jsonschema

from verif_json_schema import input_schema

results = {}

_input = json.load(sys.stdin)
# _input = {
#     "unknown_variables": [
#         {
#             "name": "x",
#             "sample_start": 0,
#             "sample_end": 10,
#             "num_samples": 40000,
#             "sample_spacing": "linear",
#         },
#     ],
#     "min_difference_detect_error": 0.1,
#     "expressions": [
#         "x^2",
#         "x*x",
#         "x^3",
#     ],
# }
# _input = {
#     "unknown_variables":[{
#         "name":"x",
#         "sample_start":0,
#         "sample_end":10,
#         "num_samples":10,
#         "sample_spacing":"linear"
#     }],
#     "min_difference_detect_error":0.1,
#     "expressions": [
#         "x^2", # 0
#         "x^3", # 1
#         "x^2", # 2
#         "x^2", # 3
#         "x^2", # 4
#         "", # 5
#         "x^2", # 6
#         "x^2", # 7
#         "x^2", # 8
#         "x^2", # 9
#     ]
# }

jsonschema.validate(instance=_input, schema=input_schema)

assert len(_input["unknown_variables"]) == 1, "exactly 1 unknown variable"
unknown_var = _input["unknown_variables"][0]
if unknown_var["sample_spacing"] == "linear":
    samples = np.linspace(unknown_var["sample_start"], unknown_var["sample_end"], unknown_var["num_samples"])
else:
    samples = np.geomspace(unknown_var["sample_start"], unknown_var["sample_end"], unknown_var["num_samples"])

# remove blank expressions from list
# but the user is expecting certain index numbers
# so we must convert back to be consistent with what the user sees
latex_expressions_not_blank = []
not_blank_index_2_original_index = {}
pad_index = 0
for i,expr in enumerate(_input["expressions"]):
    if expr.strip() == "":
        continue
    latex_expressions_not_blank.append(expr)
    not_blank_index_2_original_index[len(latex_expressions_not_blank)-1] = i

graphs = []
for latex_expr in latex_expressions_not_blank:
    sympy_expr = parse_latex(latex_expr)
    func = sp.lambdify(unknown_var["name"], sympy_expr, 'numpy')
    graphs.append(func(samples))

for i in range(1,len(graphs)):
    prev_graph_diff = sum(abs(graphs[i]-graphs[i-1]))
    if prev_graph_diff > _input["min_difference_detect_error"]:
        results = {
            "all-equal": False,
            "first-non-equal-indexes": [not_blank_index_2_original_index[i-1], not_blank_index_2_original_index[i]],
            "x-axis-array": samples.tolist(),
            "y-axis-array1": graphs[i-1].tolist(),
            "y-axis-array2": graphs[i].tolist(),
        }
        break

if results == {}:
    results = {"all-equal": True}

print(json.dumps(results))
