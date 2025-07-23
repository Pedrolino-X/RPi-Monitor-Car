#!/bin/bash
# This script deactivates AP mode, reconnects to WiFi, and saves the state.

echo "Saving 'sta' state..."
sudo mkdir -p /etc/network
echo "sta" | sudo tee /etc/network/mode.state > /dev/null

echo "Deactivating AP mode..."
nmcli connection down MyPiAP 2>/dev/null || true

echo "Connecting to the best available WiFi network..."
nmcli device wifi connect "$(nmcli -t -f SSID,IN-USE d wifi list | grep -v '^*' | head -n 1 | cut -d: -f1)" 

echo ""
echo "✅ STA Mode is active."
