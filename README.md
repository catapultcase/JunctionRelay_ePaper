# JunctionRelay ePaper Node

A Python-based e-paper display renderer for JunctionRelay sensor data. Designed for Raspberry Pi (tested on Pi 5) with a 5.79" Waveshare color e-paper display (epd5in79g).

---

## 📦 Features

- Real-time sensor rendering from JunctionRelay payloads
- Dynamic screen updates
- Headless safe mode (saves image for preview if no hardware)
- Fully self-contained (no Docker required)

---

## ⚙️ Hardware Requirements

- Raspberry Pi (Pi 5 recommended)
- Waveshare 5.79" Color e-Paper (Model: **epd5in79g**)
- SPI and GPIO pins connected as per Waveshare wiring guide

---

## 🚀 Installation Instructions

### 1. Clone this repository

```bash
git clone https://github.com/catapultcase/JunctionRelay_ePaper
cd JunctionRelay_ePaper
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask
- Pillow
- psutil
- gpiozero
- spidev
- RPi.GPIO
- waveshare-epaper (if present on PyPI)
- all other necessary packages

> ⚠️ `RPi.GPIO` and `psutil` may show deprecation warnings during install — these are safe to ignore for now.

---

## 📁 Optional: Add the actual e-Paper driver (if not using PyPI version)

If you want to bundle the latest **Waveshare drivers** directly from source:

```bash
git clone https://github.com/waveshareteam/e-Paper.git temp_epd
cp -r temp_epd/RaspberryPi_JetsonNano/python/lib/waveshare_epd ./waveshare_epd
rm -rf temp_epd
touch waveshare_epd/__init__.py  # Ensures it’s a valid package
```

> If you get import errors from `sensor_display.py`, make sure to use:
> ```python
> import waveshare_epd.epd5in79g as epd5in79g
> ```

---

## 🖥️ Run the app

```bash
python main.py
```

- On first launch, you’ll see a JunctionRelay startup screen.
- When sensor payloads are received, the screen updates.
- If hardware is not detected, an image will be saved to your temp folder (`/tmp/epaper_display.png`).

---

## 🧪 Test Without Hardware

You can run the app on any system (like macOS or a Pi without the display) and it will render to an image for debugging.

---

## 🛑 Exiting

To deactivate the virtual environment:

```bash
deactivate
```

---

## 📜 License

This project is released under the GPLv3 license.
