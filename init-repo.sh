#!/bin/bash

set -e  # Exit on error

echo "==== Initializing Git Repository ===="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git and try again."
    exit 1
fi

# Check if we're already in a git repository
if git rev-parse --is-inside-work-tree &> /dev/null; then
    echo "Already in a Git repository. Skipping initialization."
else
    # Initialize new repository
    echo "Initializing new Git repository..."
    git init
    git branch -m main
    
    # Add all files
    git add .
    
    # Make initial commit
    git commit -m "Initial commit: MCP Audio Server project scaffold"
    
    echo "Git repository initialized with initial commit on 'main' branch."
fi

# Instructions for setting up remote
echo ""
echo "Next steps:"
echo "1. Create a repository on GitHub/GitLab/etc."
echo "2. Add the remote to this repository:"
echo "   git remote add origin <repository-url>"
echo "3. Push to the remote repository:"
echo "   git push -u origin main"
