#!/bin/bash
# This script disables the server from being auto-started by NetworkManager.

echo "--- Disabling Server Autostart ---"
sudo systemctl stop my-server.service
sudo systemctl disable my-server.service
sudo systemctl daemon-reload

echo ""
echo "✅ Done. The server.py script will no longer be started automatically."
