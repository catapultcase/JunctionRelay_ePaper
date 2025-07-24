#!/bin/bash

# E-Paper Junction Relay Installation Script

set -e

echo "Installing E-Paper Junction Relay..."

# Update system
sudo apt update

# Install system dependencies
sudo apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    libfreetype6-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff5 \
    fonts-dejavu-core \
    git \
    curl

# Enable SPI
sudo raspi-config nonint do_spi 0

# Install Python dependencies
pip3 install -r requirements.txt

# Create service directories
sudo mkdir -p /opt/epaper-junction-relay
sudo cp -r . /opt/epaper-junction-relay/
sudo chown -R pi:pi /opt/epaper-junction-relay

# Create systemd service
sudo tee /etc/systemd/system/epaper-junction-relay.service > /dev/null <<EOF
[Unit]
Description=E-Paper Junction Relay
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/epaper-junction-relay
ExecStart=/usr/bin/python3 /opt/epaper-junction-relay/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable epaper-junction-relay
sudo systemctl start epaper-junction-relay

echo "Installation complete!"
echo "Service status: sudo systemctl status epaper-junction-relay"
echo "View logs: sudo journalctl -u epaper-junction-relay -f"
echo "Test endpoint: curl http://localhost:5000/api/health/heartbeat"