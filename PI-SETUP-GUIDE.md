\# Raspberry Pi Setup Guide for E-Paper Junction Relay



\## Prerequisites on Raspberry Pi



\### 1. Enable SPI Interface

```bash

sudo raspi-config

\# Navigate to: Interfacing Options -> SPI -> Enable

\# Or run: sudo raspi-config nonint do\_spi 0

```



\### 2. Install Waveshare E-Paper Library

```bash

\# Create library directory

sudo mkdir -p /opt/epaper/lib



\# Download Waveshare library

cd /tmp

git clone https://github.com/waveshare/e-Paper.git

sudo cp -r e-Paper/RaspberryPi\_JetsonNano/python/lib/\* /opt/epaper/lib/



\# Set permissions

sudo chown -R pi:pi /opt/epaper

```



\### 3. Install Docker (if not already installed)

```bash

\# Install Docker

curl -fsSL https://get.docker.com -o get-docker.sh

sudo sh get-docker.sh



\# Add user to docker group

sudo usermod -aG docker pi



\# Start Docker service

sudo systemctl enable docker

sudo systemctl start docker



\# Reboot to apply group changes

sudo reboot

```



\## Deployment Options



\### Option 1: Portainer Stack (Recommended)



1\. \*\*Open Portainer\*\* in your browser

2\. \*\*Go to Stacks\*\* -> Add Stack

3\. \*\*Copy the content from `portainer-stack.yml`\*\*

4\. \*\*Set Environment Variables:\*\*

&nbsp;  - `DEVICE\_NAME`: `EPaper-Kitchen` (or your preference)

&nbsp;  - `HTTP\_PORT`: `80`

&nbsp;  - `LOG\_LEVEL`: `INFO`

5\. \*\*Deploy the Stack\*\*



\### Option 2: Docker Compose



1\. \*\*Create project directory:\*\*

```bash

mkdir ~/epaper-junction-relay

cd ~/epaper-junction-relay

```



2\. \*\*Copy docker-compose.yml to Pi\*\*



3\. \*\*Deploy:\*\*

```bash

docker-compose up -d

```



\### Option 3: Direct Docker Run



```bash

docker run -d \\

&nbsp; --name epaper-junction-relay \\

&nbsp; --privileged \\

&nbsp; -p 80:80 \\

&nbsp; --device=/dev/spidev0.0:/dev/spidev0.0 \\

&nbsp; --device=/dev/gpiomem:/dev/gpiomem \\

&nbsp; -v /opt/epaper/lib:/app/lib:ro \\

&nbsp; --restart unless-stopped \\

&nbsp; junctionrelay/epaper-display:latest

```



\## Hardware Connection



\### Waveshare 5.79" G Display to Raspberry Pi



| E-Paper Pin | Pi Pin | Pi GPIO |

|-------------|--------|---------|

| VCC         | 17     | 3.3V    |

| GND         | 20     | Ground  |

| DIN         | 19     | GPIO 10 (MOSI) |

| CLK         | 23     | GPIO 11 (SCLK) |

| CS          | 24     | GPIO 8 (CE0)   |

| DC          | 22     | GPIO 25 |

| RST         | 11     | GPIO 17 |

| BUSY        | 18     | GPIO 24 |



\## Verification



\### 1. Check Container Status

```bash

docker ps

```



\### 2. Check Logs

```bash

docker logs epaper-junction-relay

```



\### 3. Test API Endpoints

```bash

\# Health check

curl http://localhost/api/health/heartbeat



\# Device info

curl http://localhost/api/device/info



\# Send test data

curl -X POST http://localhost/api/data \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{"type":"sensor","screenId":"onboard\_screen","sensors":{"test\_sensor":\[{"Value":"100","Unit":"%"}]}}'

```



\### 4. Check E-Paper Display

The display should show:

\- Junction Relay branding

\- Live sensor data in top-right corner

\- Current time



\## Troubleshooting



\### SPI Permission Issues

```bash

\# Add user to SPI group

sudo usermod -aG spi pi



\# Check SPI devices

ls -la /dev/spi\*

```



\### GPIO Permission Issues

```bash

\# Add user to GPIO group

sudo usermod -aG gpio pi

```



\### Container Not Starting

```bash

\# Check detailed logs

docker logs --details epaper-junction-relay



\# Run container interactively for debugging

docker run -it --rm \\

&nbsp; --privileged \\

&nbsp; --device=/dev/spidev0.0:/dev/spidev0.0 \\

&nbsp; junctionrelay/epaper-display:latest bash

```



\### E-Paper Library Issues

```bash

\# Verify library installation

ls -la /opt/epaper/lib/waveshare\_epd/



\# Test library directly

python3 -c "

import sys

sys.path.append('/opt/epaper/lib')

from waveshare\_epd import epd5in79g

print('Library loaded successfully')

"

```



\## Configuration



\### Environment Variables



\- `DEVICE\_NAME`: Device identifier (default: EPaper-Display)

\- `HTTP\_PORT`: HTTP server port (default: 80)

\- `LOG\_LEVEL`: Logging level (default: INFO)



\### Persistent Storage



Data is stored in Docker volumes:

\- `epaper\_config`: Configuration files

\- `epaper\_logs`: Application logs



\## Updating



\### Update Docker Image

```bash

docker pull junctionrelay/epaper-display:latest

docker-compose down

docker-compose up -d

```



\### Or via Portainer

1\. Go to Stacks -> Your Stack

2\. Click Editor

3\. Click "Pull and redeploy"



\## Integration with Junction Relay Backend



Your backend can now send data to the Pi display exactly like ESP32 devices:



```bash

POST http://pi-ip/api/data

Content-Type: application/json



{

&nbsp; "type": "sensor",

&nbsp; "screenId": "onboard\_screen", 

&nbsp; "sensors": {

&nbsp;   "temperature": \[{"Value": "22.5", "Unit": "°C"}],

&nbsp;   "humidity": \[{"Value": "45.2", "Unit": "%"}]

&nbsp; }

}

```



The Pi will display live sensor data on the e-paper screen in real-time!

