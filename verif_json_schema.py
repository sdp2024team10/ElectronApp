input_schema = {
  "$schema": "http://json-schema.org/draft-2020-12/schema#",
  "type": "object",
  "properties": {
    "unknown_variables": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "sample_start": {
            "type": "number"
          },
          "sample_end": {
            "type": "number"
          },
          "num_samples": {
            "type": "integer"
          },
          "sample_spacing": {
            "type": "string",
            "enum": ["log", "linear"]
          }
        },
        "required": ["name", "sample_start", "sample_end", "num_samples", "sample_spacing"]
      }
    },
    "min_difference_detect_error": {
      "type": "number"
    },
    "expressions": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": ["unknown_variables", "min_difference_detect_error", "expressions"]
}

output_schema = {}
