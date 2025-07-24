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
```

---

## 5. Run the application with proper GPIO backend

```bash
sudo -E env "GPIOZERO_PIN_FACTORY=lgpio" python main.py
```

> This starts the ePaper UI, initializes the display, and launches the web server at http://<your-pi-ip>:80

---

## 6. Test Access

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
