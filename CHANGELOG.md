# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 90%+ coverage
  - Unit tests for all analysis modules
  - Schema validation tests
  - End-to-end MCP tests
  - Negative-case testing for error handling
  - Fuzzy testing for edge cases
- Improved documentation
  - OpenAPI specification (docs/openapi.yaml)
  - Detailed API reference with examples
  - Architecture documentation
  - Developer environment setup guide
  - Testing guidelines
- Schema version control system
  - Support for multiple schema versions
  - Schema loader utility
  - Backward compatibility handling
- Release management tools
  - Semantic versioning enforcement
  - Automated release workflow
  - Deprecation policy
- CI/CD integration
  - GitHub Actions workflow for testing
  - Coverage reporting
  - Automated documentation building

### Changed
- Refactored validation system to support versioned schemas
- Moved schemas to version-specific directories

### Fixed
- Schema validation error handling and reporting
- Documentation inconsistencies

## [0.1.0] - 2025-04-18

### Added
- Initial release
- Basic chord detection algorithm
- Key detection
- Tempo tracking
- API endpoints for analysis
- JSON schema validation
- Error handling and reporting