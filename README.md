\# E-Paper Junction Relay



Python implementation of Junction Relay protocol for e-paper displays.



\## Features



\- \*\*Full Junction Relay Protocol Support\*\*: Handles all 4 data types

&nbsp; - Type 1: Raw JSON

&nbsp; - Type 2: Prefixed JSON  

&nbsp; - Type 3: Raw Gzip

&nbsp; - Type 4: Prefixed Gzip

\- \*\*HTTP API\*\*: Compatible endpoints with ESP32 Junction Relay devices

\- \*\*Real-time Display\*\*: Updates e-paper display with live sensor data

\- \*\*Background Processing\*\*: Queued processing for sensor and config data

\- \*\*Docker Ready\*\*: Containerized deployment

\- \*\*Hardware Support\*\*: Waveshare 5.79" G e-paper display



\## Quick Start



\### Local Development

```bash

\# Install dependencies

pip install -r requirements.txt



\# Run the service

python main.py

```



\### Docker Deployment

```bash

\# Build and run

docker-compose up -d



\# View logs

docker-compose logs -f

```



\## API Endpoints



\- `POST /api/data` - Main data ingestion (Junction Relay protocol)

\- `GET /api/device/info` - Device information

\- `GET /api/system/stats` - System statistics

\- `GET /api/connection/status` - Connection status

\- `GET /api/health/heartbeat` - Health check



\## Data Format



Send data in Junction Relay format:



```bash

\# Raw JSON (Type 1)

curl -X POST http://pi:5000/api/data \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{"type":"sensor","temperature":22.5,"humidity":45.2}'



\# Prefixed JSON (Type 2) 

\# 8-byte prefix: LLLLTTRR (length + type + route)

\# Example: 0050000 = 50 bytes, type 00 (JSON), route 00

```



\## Hardware Setup



1\. Connect Waveshare 5.79" G display to Pi SPI

2\. Enable SPI: `sudo raspi-config`

3\. Install Waveshare libraries in `lib/` directory



\## Configuration



Edit `config.json`:

```json

{

&nbsp; "display": {

&nbsp;   "refresh\_interval": 60,

&nbsp;   "theme": "default"

&nbsp; },

&nbsp; "network": {

&nbsp;   "http\_port": 5000

&nbsp; }

}

```



\## Architecture



```

Backend → HTTP POST → StreamProcessor → SensorDisplay → E-Paper

&nbsp;                   ↓

&nbsp;             \[4 Protocol Types]

```



Same architecture as ESP32 Junction Relay devices, enabling unified data flow.



\## Installation



Run the installation script:

```bash

chmod +x install.sh

./install.sh

```



Or install manually:

```bash

\# Install system dependencies

sudo apt update

sudo apt install python3 python3-pip libfreetype6-dev libjpeg-dev



\# Enable SPI

sudo raspi-config nonint do\_spi 0



\# Install Python packages

pip3 install -r requirements.txt



\# Run the service

python3 main.py

```



\## Testing



Test the API endpoints:

```bash

\# Health check

curl http://localhost:5000/api/health/heartbeat



\# Device info

curl http://localhost:5000/api/device/info



\# Send sensor data

curl -X POST http://localhost:5000/api/data \\

&nbsp; -H "Content-Type: application/json" \\

&nbsp; -d '{"type":"sensor","temperature":22.5,"humidity":45.2,"pressure":1013}'

```



\## License



MIT License - Same as Junction Relay project

