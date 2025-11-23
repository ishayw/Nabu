#!/bin/bash
# Nabu macOS Service Uninstallation Script

PLIST_INSTALL="$HOME/Library/LaunchAgents/com.nabu.meeting-summarizer.plist"

# Unload and remove the service
launchctl unload "$PLIST_INSTALL" 2>/dev/null
rm -f "$PLIST_INSTALL"

echo "✓ Nabu service uninstalled successfully!"
