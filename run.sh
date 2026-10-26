#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not reachable at http://localhost:11434"
    echo "Start it with: ollama serve"
    exit 1
fi

echo "Checking Chrome DevTools Port..."
PORT_FILE="$HOME/.config/google-chrome/DevToolsActivePort"
if [ ! -f "$PORT_FILE" ]; then
    echo "Warning: $PORT_FILE not found."
    echo "Please ensure Chrome is running with remote debugging enabled:"
    echo "  google-chrome --remote-debugging-port=9222 &"
    exit 1
fi

echo "Starting Multi-Agent Browser Assistant..."
python3 main.py "$@"
