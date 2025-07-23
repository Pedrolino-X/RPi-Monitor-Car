#!/bin/bash
# This script enables the server to be auto-started by NetworkManager when in AP mode.

echo "--- Enabling Server Autostart via NetworkManager ---"
sudo systemctl daemon-reload
sudo systemctl enable my-server.service

echo ""
echo "✅ Done. The server.py script is now enabled."
echo "It will automatically start/stop when you run start-ap.sh or start-wifi.sh."
