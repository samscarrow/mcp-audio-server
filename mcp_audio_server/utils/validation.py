"""JSON schema validation utilities."""

import json
import os
import logging
from typing import Any, Dict, Optional

# Try to import jsonschema, but don't fail if not available
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    logging.warning("jsonschema not available, validation will be skipped")
    JSONSCHEMA_AVAILABLE = False

# Directory containing JSON schemas
SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas")


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the schemas directory.
    
    Args:
        schema_name: Name of the schema file
        
    Returns:
        Loaded schema as a dictionary
    """
    schema_path = os.path.join(SCHEMAS_DIR, schema_name)
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_payload(payload: Dict[str, Any], schema_name: str) -> None:
    """
    Validate a payload against a JSON schema.
    
    Args:
        payload: Data to validate
        schema_name: Name of the schema file
        
    Raises:
        ValueError: If validation fails
    """
    if not JSONSCHEMA_AVAILABLE:
        logging.warning("Skipping validation because jsonschema is not available")
        return
    
    schema = load_schema(schema_name)
    
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"Validation error: {e.message}")
