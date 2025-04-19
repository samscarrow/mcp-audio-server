#!/usr/bin/env python
"""
Release script for MCP Audio Server.

This script automates the release process by:
1. Validating the new version
2. Updating version numbers in code
3. Updating the CHANGELOG.md
4. Creating a release branch
5. Committing changes
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date

# Constants
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGELOG_PATH = os.path.join(REPO_ROOT, "CHANGELOG.md")
SCHEMA_INDEX_PATH = os.path.join(REPO_ROOT, "schemas", "index.json")
PYPROJECT_PATH = os.path.join(REPO_ROOT, "pyproject.toml")
VERSION_PATTERN = r"^\d+\.\d+\.\d+$"


def validate_version(version: str) -> bool:
    """Validate that the version string matches semantic versioning."""
    return bool(re.match(VERSION_PATTERN, version))


def get_current_version() -> str:
    """Get the current version from pyproject.toml."""
    with open(PYPROJECT_PATH, "r") as f:
        content = f.read()

    match = re.search(r'version\s*=\s*"(\d+\.\d+\.\d+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")

    return match.group(1)


def update_pyproject(version: str) -> None:
    """Update the version in pyproject.toml."""
    with open(PYPROJECT_PATH, "r") as f:
        content = f.read()

    updated_content = re.sub(
        r'version\s*=\s*"(\d+\.\d+\.\d+)"', f'version = "{version}"', content
    )

    with open(PYPROJECT_PATH, "w") as f:
        f.write(updated_content)

    print(f"Updated version in pyproject.toml to {version}")


def update_schema_index(version: str) -> None:
    """Update the schema index with the new version."""
    with open(SCHEMA_INDEX_PATH, "r") as f:
        schema_index = json.load(f)

    # Only add the version if it doesn't already exist
    if version not in schema_index.get("schemas", {}):
        # Copy existing schemas from the current version
        current_version = schema_index.get("current_version")
        if current_version:
            schema_index["schemas"][version] = schema_index["schemas"].get(
                current_version, {}
            )

    # Update current version
    schema_index["current_version"] = version

    # Add to version history
    today = date.today().isoformat()
    next_year = date.today().replace(year=date.today().year + 1).isoformat()

    version_history = schema_index.get("version_history", [])
    for entry in version_history:
        if entry.get("version") == version:
            entry["release_date"] = today
            entry["deprecated"] = False
            entry["supported_until"] = next_year
            break
    else:
        version_history.append(
            {
                "version": version,
                "release_date": today,
                "deprecated": False,
                "supported_until": next_year,
            }
        )

    schema_index["version_history"] = version_history

    with open(SCHEMA_INDEX_PATH, "w") as f:
        json.dump(schema_index, f, indent=2)

    print(f"Updated schema index to version {version}")


def update_changelog(version: str) -> None:
    """Update the CHANGELOG.md with the new version."""
    today = date.today().isoformat()

    with open(CHANGELOG_PATH, "r") as f:
        content = f.readlines()

    # Find the "Unreleased" section
    unreleased_idx = -1
    for i, line in enumerate(content):
        if line.strip() == "## [Unreleased]":
            unreleased_idx = i
            break

    if unreleased_idx == -1:
        print("Could not find '## [Unreleased]' section in CHANGELOG.md")
        return

    # Insert the new version section after the "Unreleased" section
    version_section = f"\n## [{version}] - {today}\n"

    # Find the next section to determine the end of the "Unreleased" section
    next_section_idx = -1
    for i in range(unreleased_idx + 1, len(content)):
        if content[i].startswith("## ["):
            next_section_idx = i
            break

    if next_section_idx == -1:
        print("Could not find next section after '## [Unreleased]' in CHANGELOG.md")
        return

    # Create a new "Unreleased" section
    new_unreleased = ["## [Unreleased]\n", "\n"]

    # Copy content from the old "Unreleased" section to the new version section
    new_content = (
        content[: unreleased_idx + 1]
        + new_unreleased
        + [version_section]
        + content[unreleased_idx + 1 : next_section_idx]
        + content[next_section_idx:]
    )

    with open(CHANGELOG_PATH, "w") as f:
        f.writelines(new_content)

    print(f"Updated CHANGELOG.md with version {version}")


def create_release_branch(version: str) -> None:
    """Create a release branch for the new version."""
    branch_name = f"release/v{version}"

    # Check if the branch already exists
    result = subprocess.run(
        ["git", "branch", "--list", branch_name], capture_output=True, text=True
    )

    if branch_name in result.stdout:
        print(f"Branch {branch_name} already exists")
        return

    # Create the branch
    subprocess.run(["git", "checkout", "-b", branch_name])
    print(f"Created branch {branch_name}")


def commit_changes(version: str) -> None:
    """Commit the changes to the release branch."""
    # Add the files
    subprocess.run(["git", "add", PYPROJECT_PATH, SCHEMA_INDEX_PATH, CHANGELOG_PATH])

    # Commit
    subprocess.run(["git", "commit", "-m", f"chore: prepare release v{version}"])
    print(f"Committed changes for version {version}")


def main():
    parser = argparse.ArgumentParser(description="Create a new release")
    parser.add_argument("version", help="New version number (MAJOR.MINOR.PATCH)")
    args = parser.parse_args()

    version = args.version

    # Validate the version
    if not validate_version(version):
        print(f"Invalid version format: {version}. Expected MAJOR.MINOR.PATCH")
        sys.exit(1)

    current_version = get_current_version()
    print(f"Current version: {current_version}")
    print(f"New version: {version}")

    # Confirm with the user
    confirmation = input("Proceed with release? [y/N] ")
    if confirmation.lower() != "y":
        print("Release cancelled")
        sys.exit(0)

    # Update files
    update_pyproject(version)
    update_schema_index(version)
    update_changelog(version)

    # Create branch and commit changes
    create_release_branch(version)
    commit_changes(version)

    print("\nRelease preparation complete!")
    print(f"Branch: release/v{version}")
    print("\nNext steps:")
    msg = (
        "1. Review the changes\n"
        f"2. Push the branch: git push -u origin release/v{version}\n"
        "3. Create a pull request\n"
        f"4. After merging, tag the release: git tag v{version}\n"
        f"5. Push the tag: git push origin v{version}"
    )
    print(msg)


if __name__ == "__main__":
    main()
