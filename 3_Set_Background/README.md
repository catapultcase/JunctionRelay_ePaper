# JunctionRelay ePaper – Installation Guide

This guide assumes:
- You're using a Raspberry Pi (64-bit OS)
- You want to run the ePaper UI on a Waveshare 5.79" display
- You want clean install instructions that work without manual patching

---

## 1. Clone the project and enter it

```bash
git clone https://github.com/jonmillsdev/JunctionRelay_ePaper.git
cd JunctionRelay_ePaper
```

---

## 2. Create a virtual environment and activate it

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install required system packages

```bash
sudo apt update
sudo apt install -y python3-lgpio python3-pip libopenjp2-7
```

---

## 4. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install lgpio==0.2.2.0
pip install waveshare-epaper==1.3.0
```

---

## 5. Install Waveshare e-paper library

```bash
git clone https://github.com/waveshare/e-Paper.git
cp -r e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd ./
```

> Note: Permission errors for __pycache__ files during copy are normal and can be ignored.

---

## 6. Run the application with proper GPIO backend

```bash
sudo -E env "GPIOZERO_PIN_FACTORY=lgpio" python main.py
```

> This starts the ePaper UI, initializes the display, and launches the web server at http://<your-pi-ip>:80

---

## 7. Test Access

From your browser (on same LAN):

```
http://<your-raspberry-pi-ip>:80
```

---

## ✅ DONE

The ePaper display should now:
- Power on
- Show sensor display layout
- Be reachable via HTTP
- Auto-refresh when updates arrive

---

## Enhanced Features (if using enhanced sensor_display.py)

The enhanced version supports:
- **Background Images**: Upload via `/api/display/background` endpoint
- **Background Colors**: Set via `/api/display/background/color` endpoint  
- **Styling Updates**: Modify element appearance via `/api/display/styles`
- **Web Interface**: Built-in test interface at `http://your-pi-ip/`

### Test Background Color
```bash
curl -X POST http://your-pi-ip/api/data \
  -H "Content-Type: application/json" \
  -d '{"type":"sensor","background_color":[173,216,230],"sensors":{"Temperature":{"value":23,"unit":"°C"}}}'
```