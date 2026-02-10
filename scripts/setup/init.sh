#!/bin/bash

# DCIS Project Setup Script
set -e

echo "🚀 DCIS Project Setup"
echo "===================="

# Install Poetry if not present
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✓ Poetry already installed"
fi

# Install pnpm if not present
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
else
    echo "✓ pnpm already installed"  
fi

# Backend setup
echo ""
echo "📦 Setting up backend..."
cd backend
poetry install
cd ..

# Frontend setup
echo ""
echo "📦 Setting up frontend..."
cd frontend
pnpm install
cd ..

# Pre-commit hooks
echo ""
echo "🪝 Installing pre-commit hooks..."
pip3 install pre-commit
pre-commit install

# Environment files
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env"
fi

echo ""
echo "✅ Setup complete! Run 'make docker-up' to start services."
