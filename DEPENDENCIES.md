# Dependencies

This document lists all dependencies used in the MCP Audio Server project, their licenses, and the rationale for their inclusion.

## Runtime Dependencies

| Package    | Version   | License | Rationale                                                |
|------------|-----------|---------|----------------------------------------------------------|
| fastapi    | ^0.110.0  | MIT     | High-performance API framework with automatic validation |
| uvicorn    | ^0.27.0   | BSD     | ASGI server for FastAPI                                 |
| pydantic   | ^2.6.0    | MIT     | Data validation and settings management                  |
| numpy      | ^1.26.0   | BSD     | Scientific computing and array processing                |
| librosa    | ^0.10.1   | ISC     | Audio analysis, feature extraction, and chord detection  |
| jsonschema | ^4.20.0   | MIT     | JSON schema validation                                   |

## Development Dependencies

| Package | Version | License | Rationale                              |
|---------|---------|---------|----------------------------------------|
| pytest  | ^7.4.0  | MIT     | Testing framework                      |
| black   | ^23.7.0 | MIT     | Code formatting                        |
| isort   | ^5.12.0 | MIT     | Import sorting                         |
| mypy    | ^1.5.0  | MIT     | Static type checking                   |

## License Audit

All dependencies use permissive licenses (MIT, BSD, ISC) that are compatible with commercial use and redistribution.

## Upgrade Process

To upgrade a dependency:

1. Update the version constraint in `pyproject.toml`:
   ```bash
   poetry update <package-name>
   ```

2. Run tests to ensure compatibility:
   ```bash
   pytest
   ```

3. Update this document with any version changes or new dependencies.

## Review Schedule

Dependencies should be reviewed and updated quarterly, with special attention to security advisories and breaking changes.

## CI Verification

Our CI pipeline includes automated license checks to ensure no dependencies with incompatible licenses are introduced. This is handled by the license check step in the GitHub Actions workflow.
