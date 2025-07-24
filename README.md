# JunctionRelay ePaper - Install Guide (Clean Setup)

This guide walks you through a fresh installation of the JunctionRelay ePaper Python application on a Raspberry Pi (or compatible SBC).

---

## ✅ Prerequisites

- Python 3.11+ installed
- Git installed
- Raspberry Pi OS (or compatible)
- Terminal access with sudo

---

## 🧰 Step-by-Step Installation

### 1. Clone the Repository


git clone https://github.com/catapultcase/JunctionRelay_ePaper
cd JunctionRelay_ePaper



### 2. Create and Activate Virtual Environment


python3 -m venv venv
source venv/bin/activate



### 3. Clone Waveshare Driver (Local Bundle)


git clone https://github.com/waveshareteam/e-Paper.git temp_epd
cp -r temp_epd/RaspberryPi_JetsonNano/python/lib/waveshare_epd ./waveshare_epd
rm -rf temp_epd
touch waveshare_epd/__init__.py



### 4. Install Python Dependencies



pip install -r requirements.txt



### 5. Run the Application



python main.py



You should see e-paper initialization, MAC address display, and HTTP server booting on port 80.

---

## 🌐 Endpoints

- `POST /api/data` – Ingest payloads
- `GET /api/device/info` – Basic device info
- `GET /api/system/stats` – System status metrics

---

## 📓 Notes

- The `waveshare_epd` driver is bundled locally (not from PyPI).
- You **must** run as root or allow port 80 access (`sudo python main.py`) if needed.
- To persist your environment across reboots, consider adding a `systemd` service.