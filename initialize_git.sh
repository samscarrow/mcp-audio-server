#!/bin/bash

set -e  # Exit on error

echo "==== Initializing Git Repository ===="

# Initialize new repository
git init
git branch -m main

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit: MCP Audio Server project scaffold"

echo "Git repository initialized with initial commit on 'main' branch."
echo ""
echo "Next steps:"
echo "1. Create a repository on GitHub/GitLab/etc."
echo "2. Add the remote to this repository:"
echo "   git remote add origin <repository-url>"
echo "3. Push to the remote repository:"
echo "   git push -u origin main"
