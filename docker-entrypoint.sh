#!/bin/bash
# Docker entrypoint script for Apertutus backend

set -e

echo "🚀 Starting Apertutus Backend Container..."

# Check if config.json exists
if [ ! -f "/app/config.json" ]; then
    echo "⚠️  Warning: config.json not found. Please mount your configuration file."
    echo "💡 Example: docker run -v $(pwd)/config.json:/app/config.json ..."
    
    if [ -f "/app/config_example.json" ]; then
        echo "📋 Using config_example.json as fallback (you'll need to add real API keys)"
        cp /app/config_example.json /app/config.json
    fi
fi

# Create necessary directories
mkdir -p logs outputs temp

# Set permissions
chmod +x /app/*.sh

echo "✅ Backend container ready!"
echo "🔧 Available commands:"
echo "   python main.py --help"
echo "   python main.py --translate"
echo "   python main.py --test"
echo "   python main.py --test --languages kor.Hang fra.Latn"

# Execute the provided command, or start an interactive shell
if [ $# -eq 0 ]; then
    echo "🐚 Starting interactive shell..."
    exec /bin/bash
else
    exec "$@"
fi
