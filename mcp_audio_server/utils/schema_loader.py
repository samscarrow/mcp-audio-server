"""Schema loader utility for versioned JSON schemas."""

import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Constants
SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas"
)
INDEX_PATH = os.path.join(SCHEMA_DIR, "index.json")


def get_schema_path(schema_name: str, version: Optional[str] = None) -> str:
    """
    Get the path to a schema file.

    Args:
        schema_name: The name of the schema
        version: The schema version, or None for the current version

    Returns:
        The absolute path to the schema file

    Raises:
        ValueError: If the schema or version is not found
    """
    try:
        # Load the index file
        with open(INDEX_PATH, "r") as f:
            index = json.load(f)

        # Determine the version to use
        if version is None:
            version = index.get("current_version")
            if version is None:
                raise ValueError("No current version defined in schema index")

        # Find the schema
        version_schemas = index.get("schemas", {}).get(version)
        if version_schemas is None:
            raise ValueError(f"Schema version {version} not found")

        schema_path = version_schemas.get(schema_name)
        if schema_path is None:
            raise ValueError(f"Schema {schema_name} not found in version {version}")

        # Construct the absolute path
        abs_path = os.path.join(SCHEMA_DIR, schema_path)
        if not os.path.exists(abs_path):
            raise ValueError(f"Schema file not found: {abs_path}")

        return abs_path

    except FileNotFoundError:
        logger.error(f"Schema index file not found: {INDEX_PATH}")
        raise ValueError(f"Schema index file not found: {INDEX_PATH}")

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in schema index file: {INDEX_PATH}")
        raise ValueError(f"Invalid JSON in schema index file: {INDEX_PATH}")


def load_schema(schema_name: str, version: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a schema from a file.

    Args:
        schema_name: The name of the schema
        version: The schema version, or None for the current version

    Returns:
        The schema as a dictionary

    Raises:
        ValueError: If the schema or version is not found
    """
    schema_path = get_schema_path(schema_name, version)

    try:
        with open(schema_path, "r") as f:
            return json.load(f)

    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise ValueError(f"Schema file not found: {schema_path}")

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in schema file: {schema_path}")
        raise ValueError(f"Invalid JSON in schema file: {schema_path}")


def get_supported_versions() -> Dict[str, Dict[str, Any]]:
    """
    Get a dictionary of supported schema versions and their metadata.

    Returns:
        A dictionary mapping version strings to metadata dictionaries
    """
    try:
        with open(INDEX_PATH, "r") as f:
            index = json.load(f)

        versions = {}
        for version_info in index.get("version_history", []):
            version = version_info.get("version")
            if version and not version_info.get("deprecated", False):
                versions[version] = version_info

        return versions

    except (FileNotFoundError, json.JSONDecodeError):
        logger.error(f"Failed to load schema index: {INDEX_PATH}")
        return {}


def get_current_version() -> str:
    """
    Get the current schema version.

    Returns:
        The current schema version string

    Raises:
        ValueError: If the current version cannot be determined
    """
    try:
        with open(INDEX_PATH, "r") as f:
            index = json.load(f)

        current_version = index.get("current_version")
        if current_version is None:
            raise ValueError("No current version defined in schema index")

        return current_version

    except (FileNotFoundError, json.JSONDecodeError):
        logger.error(f"Failed to load schema index: {INDEX_PATH}")
        raise ValueError(f"Failed to load schema index: {INDEX_PATH}")
