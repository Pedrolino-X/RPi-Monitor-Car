#!/bin/bash
# This script activates the AP mode and saves the state.

echo "WARNING: This will disconnect you from your current WiFi network."
echo "Activating AP mode in 3 seconds... (Press Ctrl+C to cancel)"
sleep 3

echo "Saving 'ap' state..."
sudo mkdir -p /etc/network
echo "ap" | sudo tee /etc/network/mode.state > /dev/null

echo "Bringing down existing WiFi connection..."
nmcli connection down "$(nmcli -t -f NAME,DEVICE,STATE c show --active | grep wlan0 | cut -d: -f1)" 2>/dev/null || true

echo "Starting AP hotspot (MyPiAP)..."
nmcli connection up MyPiAP

echo ""
echo "✅ AP Mode is active."
