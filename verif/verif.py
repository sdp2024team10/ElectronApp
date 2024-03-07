#!/usr/bin/env python3
import sys
import json
import numpy as np
import sympy as sp
from sympy.parsing.latex import parse_latex

# from enforce_typing import enforce_types
import jsonschema

from verif.verif_json_schema import input_schema

results = {}

_input = json.load(sys.stdin)

jsonschema.validate(instance=_input, schema=input_schema)

assert len(_input["unknown_variables"]) == 1, "exactly 1 unknown variable"
unknown_var = _input["unknown_variables"][0]
if unknown_var["sample_spacing"] == "linear":
    samples = np.linspace(
        unknown_var["sample_start"], unknown_var["sample_end"], unknown_var["num_samples"]
    )
else:
    samples = np.geomspace(
        unknown_var["sample_start"], unknown_var["sample_end"], unknown_var["num_samples"]
    )

# remove blank expressions from list
# but the user is expecting certain index numbers
# so we must convert back to be consistent with what the user sees
latex_expressions_not_blank = []
not_blank_index_2_original_index = {}
pad_index = 0
for i, expr in enumerate(_input["expressions"]):
    if expr.strip() == "":
        continue
    latex_expressions_not_blank.append(expr)
    not_blank_index_2_original_index[len(latex_expressions_not_blank) - 1] = i

graphs = []
for latex_expr in latex_expressions_not_blank:
    sympy_expr = parse_latex(latex_expr)
    func = sp.lambdify(unknown_var["name"], sympy_expr, "numpy")
    graphs.append(func(samples))

for i in range(1, len(graphs)):
    prev_graph_diff = sum(abs(graphs[i] - graphs[i - 1]))
    if prev_graph_diff > _input["min_difference_detect_error"]:
        equation1 = latex_expressions_not_blank[i - 1]
        equation2 = latex_expressions_not_blank[i]
        results = {
            "all-equal": False,
            "equation1": equation1,
            "equation2": equation2,
            "first-non-equal-indexes": [
                not_blank_index_2_original_index[i - 1],
                not_blank_index_2_original_index[i],
            ],
            "x-axis-array": samples.tolist(),
            "y-axis-array1": graphs[i - 1].tolist(),
            "y-axis-array2": graphs[i].tolist(),
        }
        break

if results == {}:
    results = {"all-equal": True}

print(json.dumps(results))
