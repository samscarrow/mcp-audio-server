#!/bin/bash

set -e  # Exit on error

echo "==== MCP Audio Server Bootstrap ===="
echo "Installing system dependencies..."

# Check OS and install dependencies accordingly
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux system dependencies
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            python3-pip \
            python3-dev \
            libsndfile1 \
            ffmpeg
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y \
            python3-pip \
            python3-devel \
            libsndfile \
            ffmpeg
    else
        echo "Unsupported Linux distribution. Please install dependencies manually."
        exit 1
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS system dependencies
    if command -v brew &> /dev/null; then
        brew install \
            libsndfile \
            ffmpeg
    else
        echo "Homebrew not found. Please install Homebrew and try again."
        echo "https://brew.sh/"
        exit 1
    fi
else
    echo "Unsupported operating system. Please install dependencies manually."
    exit 1
fi

echo "Installing Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
    echo 'export PATH="$HOME/.poetry/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
else
    echo "Poetry already installed. Updating..."
    poetry self update
fi

echo "Installing Python dependencies..."
poetry install

echo "Setup complete! You can now activate the virtual environment with:"
echo "  poetry shell"
echo
echo "Run the server with:"
echo "  uvicorn mcp_audio_server.main:app --reload"
