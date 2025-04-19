# Contributing to MCP Audio Server

Thank you for your interest in contributing to the MCP Audio Server project.

## Development Environment Setup

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd mcp-audio-server
   ```

2. Install development dependencies
   ```bash
   ./bootstrap.sh
   ```

3. Activate the Poetry environment
   ```bash
   poetry shell
   ```

4. Install pre-commit hooks
   ```bash
   pre-commit install
   ```

## Code Style and Standards

We use the following tools to maintain code quality:

- **Black**: For code formatting
- **Ruff**: For linting
- **MyPy**: For static type checking

Run all checks before submitting:
```bash
black .
ruff check .
mypy mcp_audio_server
```

## Pull Request Workflow

1. Create a feature branch from main:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit with descriptive messages:
   ```bash
   git commit -m "feat: add new chord detection algorithm"
   ```

3. Push your branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Create a pull request on GitHub/GitLab

### Branch Naming Convention

- `feature/description` - For new features
- `bugfix/issue-id` - For bug fixes
- `docs/description` - For documentation changes
- `refactor/description` - For code refactoring

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

## Testing

All code changes should include tests:

1. Unit tests for individual functions and modules
2. Integration tests for component interactions
3. End-to-end tests for API flows
4. Schema validation tests for data models
5. Negative test cases that verify proper error handling

### Running Tests

Run the full test suite with coverage reporting:
```bash
pytest
```

Run a specific test file:
```bash
pytest tests/test_end_to_end.py
```

Run tests with a specific marker:
```bash
pytest -m unit
```

Available markers: `unit`, `integration`, `e2e`, `functional`, `schema`, `slow`

### Test Coverage Requirements

The project maintains a minimum of 90% test coverage. Pull requests that decrease coverage below this threshold will be rejected by CI.

To view detailed coverage reports:
```bash
# Run tests with coverage
pytest

# Open HTML coverage report
open htmlcov/index.html
```

### Test Fixtures

Test fixtures are stored in the `tests/fixtures/` directory:

- `tempo/`: Audio files with known tempo values (60, 90, 120, 150 BPM)
- `key/`: Audio files in various musical keys
- `chords/`: Audio files with known chord progressions
- `edge_cases/`: Special cases for testing boundary conditions
- `errors/`: Deliberately malformed files for testing error handling

To generate additional test fixtures:
```bash
python create_test_fixtures.py
```

## Documentation

All new features should be documented:

1. Docstrings for all public functions and classes
2. API documentation with examples
3. Update README.md for major changes
4. Update CHANGELOG.md for release-worthy changes

## Review Process

Pull requests require:
1. All tests passing
2. Code coverage maintained or improved
3. Code review from at least one maintainer
4. No unresolved comments
