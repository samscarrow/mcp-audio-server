# Getting Started for Developers

This guide will help you set up a development environment for the MCP Audio Server and get familiar with the codebase.

## Prerequisites

Before you begin, make sure you have the following installed:

1. **Python 3.10+**
2. **FFmpeg**: Required for audio processing
3. **Poetry**: For dependency management
4. **Git**: For version control

## Setup Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mcp-audio-server.git
   cd mcp-audio-server
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Activate the poetry shell:
   ```bash
   poetry shell
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Generate audio test fixtures:
   ```bash
   python create_test_fixtures.py
   ```

## Project Structure

```
mcp-audio-server/
├── mcp_audio_server/     # Main package
│   ├── __init__.py
│   ├── analysis/         # Audio analysis modules
│   │   ├── chord_detection.py
│   │   ├── key_detection.py
│   │   ├── tempo_tracking.py
│   │   └── models.py
│   ├── audio_io.py       # Audio I/O utilities
│   ├── cache.py          # Caching implementation
│   ├── concurrency.py    # Concurrency controls
│   ├── main.py           # FastAPI application
│   ├── metrics.py        # Prometheus metrics
│   └── utils/            # Utility functions
├── tests/                # Test suite
│   ├── fixtures/         # Audio test fixtures
│   ├── analysis/         # Tests for analysis modules
│   └── test_*.py         # Various test modules
├── schemas/              # JSON schemas
├── docs/                 # Documentation
├── docker-compose.yml    # Docker Compose configuration
├── Dockerfile            # Docker build configuration
├── pyproject.toml        # Poetry configuration
└── README.md             # Project overview
```

## Running the Server

Start the server in development mode:

```bash
uvicorn mcp_audio_server.main:app --reload
```

The server will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics (redirects to the metrics dashboard)

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov-report=html
open htmlcov/index.html
```

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**: Implement your feature or fix

3. **Run code formatting**:
   ```bash
   black .
   ruff check .
   mypy mcp_audio_server
   ```

4. **Run tests**:
   ```bash
   pytest
   ```

5. **Commit your changes**:
   ```bash
   git commit -m "feat: add new feature"
   ```

6. **Push your branch**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

7. **Create a pull request**: Open a PR against the main branch

## Building Documentation

Build and serve the documentation locally:

```bash
mkdocs serve
```

Then open http://localhost:8000 in your browser.

## Docker Development

For development with Docker:

```bash
# Build the development image
docker compose build

# Start the server in development mode
docker compose up

# Run tests in the container
docker compose exec app pytest
```

## Next Steps

- Read [CONTRIBUTING.md](contributing.md) for detailed contribution guidelines
- Review the [Architecture](../architecture.md) documentation to understand the system design
- Check out [ENV.md](environment.md) for information on configuration options
