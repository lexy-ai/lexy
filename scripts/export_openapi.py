"""Export OpenAPI spec from Lexy Server to JSON file for use in MkDocs"""

import json
from lexy.main import app


# Path of the openapi json file used by mkdocs
openapi_json_path = "docs/docs/reference/rest-api/openapi.json"

# Get OpenAPI schema as a dictionary
openapi_dict = app.openapi()

# Write OpenAPI schema to JSON file
with open(openapi_json_path, "w") as f:
    json.dump(openapi_dict, f)

print(f"OpenAPI schema written to {openapi_json_path}")
