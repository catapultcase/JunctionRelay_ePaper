# JunctionRelay ePaper

A 4-color e-paper dashboard client for Raspberry Pi using the **Waveshare 5.79" display (epd5in79g)**.  
Displays live sensor data via the JunctionRelay protocol and hosts an HTTP API for inbound communication.

---

## ✨ Features

- Supports Waveshare 5.79" 4-color e-paper (black, white, red, yellow)
- Renders real-time sensor values on screen
- Includes system stats, startup screen, and color-coded layout
- HTTP API with configurable data ingestion
- Fully native Python — no Docker needed

---

## 🧰 Requirements

- Raspberry Pi (Zero, 3, 4, 5) with Raspberry Pi OS
- Waveshare 5.79" e-Paper Display (model `epd5in79g`)
- SPI enabled in Pi config
- Python 3.7 or newer

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/catapultcase/JunctionRelay_ePaper.git
cd JunctionRelay_ePaper
```

---

### 2. Enable SPI

```bash
sudo raspi-config
# → Interface Options → SPI → Enable → Reboot if prompted
```

---

### 3. Install dependencies

```bash
sudo apt update
sudo apt install python3-pip fonts-dejavu
pip3 install -r requirements.txt
```

---

### 4. Install Waveshare driver (required once)

Create the driver directory and download the two required files:

```bash
mkdir -p lib/waveshare_epd
cd lib/waveshare_epd

wget https://raw.githubusercontent.com/waveshare/e-Paper/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd5in79g.py
wget https://raw.githubusercontent.com/waveshare/e-Paper/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epdconfig.py
```

---

### 5. Run the application

You **must use sudo** to:
- Bind to port 80
- Access `/dev/spidev*` and `/dev/gpiomem*`

```bash
cd ~/JunctionRelay_ePaper
sudo python3 main.py
```

---

## ✅ Result

- Your e-paper display will show the startup layout
- HTTP server will run on port `80`
- Accepts:
  - `POST /api/data` — Ingests sensor/config data
  - `GET  /api/device/info` — Returns device info
  - `GET  /api/system/stats` — Returns status

---

## 📄 `requirements.txt`

```
Flask==2.3.3
Pillow==10.0.1
psutil==5.9.0
gpiozero==1.6.2
spidev
RPi.GPIO
```

---

## ⚠️ Notes

- This project does **not** use Docker (on purpose) — native Pi support is simpler and more robust
- A wrapper (`epaper_wrapper.py`) manages hardware access and ensures fallback-friendly startup
- If you don’t use port 80, modify `http_endpoints.py` to change the server port

---

## 🔁 Optional: Auto-start on boot

If you'd like this to run at startup, you can create a `systemd` service.  
Let us know and we can provide a ready-made file.

---

## 📸 Screenshot

*Coming soon: preview of live sensor dashboard*

---

## 🪪 License

MIT or GPL-3 — pick your preferred license.

---

## 👋 Credits

Created by [@catapultcase](https://github.com/catapultcase) for the JunctionRelay ecosystem.