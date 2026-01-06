#!/bin/bash

# Authority Boundary Ledger - Quick Start Script

echo "=================================="
echo "Authority Boundary Ledger Demo"
echo "=================================="
echo ""

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY environment variable not set"
    echo ""
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    echo "Or create a .env file:"
    echo "  cp .env.example .env"
    echo "  # Edit .env and add your key"
    echo ""
    exit 1
fi

echo "✅ API key detected"
echo ""

# Check if dependencies are installed
if ! python -c "import anthropic" 2>/dev/null; then
    echo "❌ Dependencies not installed"
    echo ""
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

echo "Select demo to run:"
echo "  1) Enterprise Database Demo (recommended)"
echo "  2) Simple Info-Only Demo"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "Running Enterprise Database Demo..."
        echo ""
        python demo_database.py
        ;;
    2)
        echo ""
        echo "Running Simple Demo..."
        echo ""
        python demo.py
        ;;
    *)
        echo "Invalid choice. Running database demo by default..."
        python demo_database.py
        ;;
esac
