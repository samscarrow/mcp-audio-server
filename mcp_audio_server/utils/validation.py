"""JSON schema validation utilities."""

import json
import os
import logging
from typing import Any, Dict, Optional

from mcp_audio_server.utils.schema_loader import load_schema as load_versioned_schema

# Try to import jsonschema, but don't fail if not available
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    logging.warning("jsonschema not available, validation will be skipped")
    JSONSCHEMA_AVAILABLE = False

# Directory containing JSON schemas
SCHEMAS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas"
)

logger = logging.getLogger(__name__)


def _load_legacy_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the legacy (non-versioned) schemas directory.
    
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


def validate_payload(
    payload: Dict[str, Any], schema_name: str, version: Optional[str] = None
) -> None:
    """
    Validate a payload against a JSON schema.
    
    Args:
        payload: Data to validate
        schema_name: Name of the schema (e.g., 'audio_analysis_response')
        version: Schema version to use, or None for the current version
        
    Raises:
        ValueError: If validation fails
    """
    if not JSONSCHEMA_AVAILABLE:
        logger.warning("Skipping validation because jsonschema is not available")
        return
    
    try:
        # First try to load versioned schema
        schema = load_versioned_schema(schema_name, version)
    except ValueError as e:
        # If not found, try legacy schema
        logger.warning(
            f"Failed to load versioned schema: {e}. Falling back to legacy schema."
        )
        try:
            schema = _load_legacy_schema(schema_name)
        except FileNotFoundError:
            logger.error(f"Schema not found: {schema_name}")
            raise ValueError(f"Schema not found: {schema_name}")
    
    try:
        jsonschema.validate(instance=payload, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        message = f"Validation error: {e.message}"
        logger.error(message)
        raise ValueError(message)
    
    logger.debug(f"Validation successful for schema: {schema_name}")


def validate_payload_for_all_versions(
    payload: Dict[str, Any], schema_name: str
) -> Dict[str, bool]:
    """
    Validate a payload against all available schema versions.
    
    Args:
        payload: Data to validate
        schema_name: Name of the schema
        
    Returns:
        Dictionary mapping version strings to validation results
        (True for valid, False for invalid)
    """
    if not JSONSCHEMA_AVAILABLE:
        logger.warning("Skipping validation because jsonschema is not available")
        return {}
    
    from mcp_audio_server.utils.schema_loader import get_supported_versions
    
    results = {}
    for version in get_supported_versions().keys():
        try:
            validate_payload(payload, schema_name, version)
            results[version] = True
        except ValueError:
            results[version] = False
    
    return results


def is_payload_valid(
    payload: Dict[str, Any], schema_name: str, version: Optional[str] = None
) -> bool:
    """
    Check if a payload is valid against a JSON schema without raising exceptions.
    
    Args:
        payload: Data to validate
        schema_name: Name of the schema
        version: Schema version to use, or None for the current version
        
    Returns:
        True if valid, False otherwise
    """
    try:
        validate_payload(payload, schema_name, version)
        return True
    except ValueError:
        return False
