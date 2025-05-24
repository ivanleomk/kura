"""Extract OpenAPI schema from the FastAPI app."""

import json
import os
import sys

# Set environment variable before importing the app
os.environ["KURA_CHECKPOINT_DIR"] = "./tutorial_checkpoints"

# Add parent directory to path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

from kura.explorer.backend.main import app

# Get OpenAPI schema
openapi_schema = app.openapi()

# Write to file
with open("openapi.json", "w") as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI schema saved to openapi.json")

# Also print a summary
print(f"\nAPI Title: {openapi_schema['info']['title']}")
print(f"Version: {openapi_schema['info']['version']}")
print(f"Description: {openapi_schema['info']['description']}")
print("\nEndpoints:")
for path, methods in openapi_schema["paths"].items():
    for method, details in methods.items():
        print(f"  {method.upper()} {path} - {details.get('summary', 'No summary')}")
