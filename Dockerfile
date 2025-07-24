# E-Paper Junction Relay - Production Docker Image
FROM python:3.9-slim

# Set metadata
LABEL maintainer="Junction Relay Project"
LABEL description="E-Paper Junction Relay - Python implementation for Raspberry Pi"
LABEL version="1.0.0"

# Install system dependencies for e-paper display
RUN apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    libfreetype6-dev \
    libjpeg-dev \
    libopenjp2-7 \
    libtiff-dev \
    fonts-dejavu-core \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Pi-specific packages only on ARM64 (will be installed via pip instead)
# python3-spidev and python3-rpi.gpio are not available on AMD64

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Pi-specific packages that may not be available on all platforms
RUN pip install --no-cache-dir spidev RPi.GPIO || echo "Pi-specific packages not available on this platform - using mock mode"

# Copy application code
COPY main.py .
COPY stream_processor.py .
COPY http_endpoints.py .
COPY sensor_display.py .
COPY device_config.py .
COPY utils.py .
COPY epaper_wrapper.py .

# Create directories for Waveshare library and configuration
RUN mkdir -p /app/lib /app/config /app/logs

# Note: Waveshare libraries should be mounted at runtime via volume
# For development/testing without hardware, the mock display will be used

# Set Python path to include lib directory
ENV PYTHONPATH="/app:/app/lib"

# Pi 5 specific environment variables
ENV GPIOZERO_PIN_FACTORY=rpigpio
ENV PIGPIO_ADDR=127.0.0.1
ENV PIGPIO_PORT=8888

# Create non-root user for security
RUN groupadd -r epaper 2>/dev/null || true
RUN useradd -r -g epaper epaper 2>/dev/null || useradd -r epaper 2>/dev/null || true  
RUN if id epaper >/dev/null 2>&1; then chown -R epaper:epaper /app; fi

# Expose port 80 (same as ESP32 devices)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/api/health/heartbeat || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Copy Pi hardware detection info into container
RUN echo "Raspberry Pi 5" > /proc/device-tree/model 2>/dev/null || true

# Run as non-root user if created successfully, otherwise run as root (will be overridden by Docker daemon user)
# USER epaper

# Start the application
CMD ["python", "main.py"]