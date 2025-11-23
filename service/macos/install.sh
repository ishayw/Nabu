#!/bin/bash
# Nabu macOS Service Installation Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PLIST_TEMPLATE="$SCRIPT_DIR/com.nabu.meeting-summarizer.plist"
PLIST_INSTALL="$HOME/Library/LaunchAgents/com.nabu.meeting-summarizer.plist"

# Find Python path
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "❌ Error: python3 not found in PATH"
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LauchAgents"

# Copy and customize plist
sed -e "s|/usr/local/bin/python3|$PYTHON_PATH|g" \
    -e "s|/path/to/meeting-summarizer|$PROJECT_DIR|g" \
    "$PLIST_TEMPLATE" > "$PLIST_INSTALL"

# Load the service
launchctl unload "$PLIST_INSTALL" 2>/dev/null || true
launchctl load "$PLIST_INSTALL"

echo "✓ Nabu service installed successfully!"
echo "The service will start automatically on login."
echo ""
echo "To check status: launchctl list | grep nabu"
echo "To stop: launchctl unload $PLIST_INSTALL"
echo "To start: launchctl load $PLIST_INSTALL"
echo "To view logs: tail -f $PROJECT_DIR/nabu.log"
