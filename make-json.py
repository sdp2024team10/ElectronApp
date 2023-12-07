#!/usr/bin/env python3
import json
output_dict = {
    "unknown_variables": [
        {
            "name": "x",
            "sample_start": 0,
            "sample_end": 10,
            "num_samples": 400,
            "sample_spacing": "linear",
        },
    ],
    "min_difference_detect_error": 0.1,
    "expressions": [
        "x^2",
        "x*x",
        "x^3",
    ],
}

print(json.dumps(output_dict))
