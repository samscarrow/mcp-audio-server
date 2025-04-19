# Contributing Guide

Thank you for your interest in contributing to the MCP Audio Server! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct:

- Be respectful and inclusive
- Focus on constructive feedback
- Respect the time and effort of maintainers
- Keep discussions technical and professional

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up your development environment (see [Getting Started](getting-started.md))
4. Create a feature branch from `main`

## Development Workflow

### Branch Naming Convention

- `feature/description` - For new features
- `bugfix/issue-id` - For bug fixes
- `docs/description` - For documentation changes
- `refactor/description` - For code refactoring
- `test/description` - For adding or updating tests

Examples:
- `feature/advanced-chord-detection`
- `bugfix/issue-42-memory-leak`
- `docs/clarify-api-response-format`

### Commit Message Format

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types include:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect code functionality
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Changes to build process or auxiliary tools

Examples:
```
feat(tempo): add beat tracking functionality

This adds beat tracking to the tempo detector, which allows for
more accurate tempo estimation and returns beat positions.

Closes #123
```

### Pull Request Process

1. Create a pull request from your feature branch to the main repository
2. Ensure all CI checks pass
3. Request review from maintainers
4. Address review feedback
5. Once approved, your PR will be merged

### PR Requirements

All pull requests must:
- Pass all CI checks
- Include appropriate tests
- Maintain or improve code coverage
- Include documentation updates for new features
- Follow the coding style guidelines

## Coding Style

The project follows these coding standards:

- [Black](https://black.readthedocs.io/) for code formatting
- [Ruff](https://docs.astral.sh/ruff/) for linting
- [MyPy](https://mypy.readthedocs.io/) for static type checking
- [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)

### Style Enforcement

```bash
# Format code with Black
black .

# Run linting with Ruff
ruff check .

# Run static type checking
mypy mcp_audio_server
```

We use pre-commit hooks to enforce these standards:

```bash
pre-commit install
```

## Testing

See [Testing Guide](testing.md) for detailed information on testing.

Every code change should include tests:
- Unit tests for new functions
- Integration tests for component interactions
- End-to-end tests for API endpoints

Run tests with coverage:

```bash
pytest --cov=mcp_audio_server
```

## Documentation

All new features should be documented:

1. Docstrings for all public functions and classes
2. Update API documentation for any API changes
3. Update README.md for major changes
4. Update CHANGELOG.md for release-worthy changes

Build documentation:

```bash
mkdocs build
```

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR: Incompatible API changes
- MINOR: Backwards-compatible functionality
- PATCH: Backwards-compatible bug fixes

Release steps:
1. Create a release branch: `release/vX.Y.Z`
2. Update version numbers in code
3. Update CHANGELOG.md
4. Create a pull request for review
5. After approval, merge and tag the release
6. Create a GitHub release with release notes

## Feature Requests and Bug Reports

- Use GitHub Issues to report bugs or request features
- Provide detailed descriptions and reproduction steps
- For bugs, include error messages and logs
- For features, explain the use case and expected behavior

## Contact

If you have questions or need help:
- Open a discussion on GitHub
- Contact the maintainers via email or Slack
