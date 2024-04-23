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

jsonschema.validate(instance=_input, schema=input_schema)

PI_STR = "3.141596"

assert len(_input["unknown_variables"]) == 1, "exactly 1 unknown variable"
unknown_var = _input["unknown_variables"][0]
if unknown_var["sample_spacing"] == "linear":
    samples = np.linspace(
        unknown_var["sample_start"],
        unknown_var["sample_end"],
        unknown_var["num_samples"],
    )
else:
    samples = np.geomspace(
        unknown_var["sample_start"],
        unknown_var["sample_end"],
        unknown_var["num_samples"],
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
    expr = expr.replace(r"\pi", PI_STR)
    latex_expressions_not_blank.append(expr)
    not_blank_index_2_original_index[len(latex_expressions_not_blank) - 1] = i

graphs = []
for latex_expr in latex_expressions_not_blank:
    sympy_expr = parse_latex(latex_expr)
    try:
        func = sp.lambdify(unknown_var["name"], sympy_expr, "numpy")
    except TypeError:
        raise RuntimeError(f'unable to convert expression to function: "{latex_expr}"')
    try:
        graphs.append(func(samples))
    except TypeError:
        raise RuntimeError(f'unable to evaluate expression "{latex_expr}"')

for i in range(1, len(graphs)):
    try:
        prev_graph_diff = float(np.sum(np.abs(graphs[i] - graphs[i - 1])))
    except TypeError as e:
        print(
            "\n".join(
                [
                    "your expression cannot be evaluated.",
                    "this can be because your expression has multiple unknown variables,",
                    "or your expression has constants such as pi.",
                ]
            ),
            file=sys.stderr,
        )
        sys.exit(1)
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
