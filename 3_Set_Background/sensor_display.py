"""
Sensor Display - Manages e-paper display updates
Handles real sensor data from Junction Relay protocol
Enhanced with background image support via config payloads
"""

import os
import time
import tempfile
import base64
import io
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

import waveshare_epd.epd5in79g as epd5in79g

class SensorDisplay:
    def __init__(self, config):
        self.config = config
        self.epd = None
        self.width = 792
        self.height = 272
        self.initialized = False

        self.sensor_data = {}
        self.last_update = None

        # Background image support
        self.background_image = None
        self.background_mode = "default"  # "default", "image", "color"
        self.background_color = (255, 255, 255)

        self.font_big = None
        self.font_medium = None
        self.font_small = None

    def initialize(self):
        try:
            self.epd = epd5in79g.EPD()
            self.epd.init()
            self.width, self.height = self.epd.width, self.epd.height
            self._load_fonts()
            self.initialized = True
            print(f"[SensorDisplay] Real e-paper display initialized: {self.width}x{self.height}")
            return True
        except Exception as e:
            print(f"[SensorDisplay] ERROR initializing e-paper: {e}")
            return False

    def _load_fonts(self):
        try:
            self.font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
            self.font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
            self.font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except Exception as e:
            print(f"[SensorDisplay] WARNING: Failed to load fonts: {e}")
            self.font_big = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def set_background_image(self, image_data: bytes, opacity: float = 1.0):
        """Set background image from binary data"""
        try:
            image = Image.open(io.BytesIO(image_data))
            image = self._resize_image_to_fit(image)
            
            if opacity < 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(opacity)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            self.background_image = image
            self.background_mode = "image"
            print(f"[SensorDisplay] Background image set: {image.size}")
            
        except Exception as e:
            print(f"[SensorDisplay] ERROR setting background image: {e}")

    def set_background_from_base64(self, base64_data: str, opacity: float = 1.0):
        """Set background image from base64 encoded data"""
        try:
            if base64_data.startswith('data:image'):
                base64_data = base64_data.split(',')[1]
                
            image_data = base64.b64decode(base64_data)
            self.set_background_image(image_data, opacity)
            
        except Exception as e:
            print(f"[SensorDisplay] ERROR setting background from base64: {e}")

    def set_background_color(self, color: Tuple[int, int, int]):
        """Set solid color background"""
        self.background_color = color
        self.background_mode = "color"
        self.background_image = None
        print(f"[SensorDisplay] Background color set: {color}")

    def clear_background(self):
        """Reset to default white background"""
        self.background_mode = "default"
        self.background_image = None
        self.background_color = (255, 255, 255)

    def _resize_image_to_fit(self, image: Image.Image) -> Image.Image:
        """Resize image to fit display while maintaining aspect ratio"""
        img_width, img_height = image.size
        display_width, display_height = self.width, self.height
        
        scale_x = display_width / img_width
        scale_y = display_height / img_height
        scale = min(scale_x, scale_y)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        canvas = Image.new('RGB', (display_width, display_height), (255, 255, 255))
        x_offset = (display_width - new_width) // 2
        y_offset = (display_height - new_height) // 2
        canvas.paste(resized, (x_offset, y_offset))
        
        return canvas

    def show_startup_screen(self):
        if not self.initialized:
            return
        image = self._create_base_canvas()
        draw = ImageDraw.Draw(image)
        self._draw_static_content(draw)
        self._draw_sensor_table(draw, {})
        self._update_display(image)
        print("[SensorDisplay] Startup screen displayed")

    def _create_base_canvas(self) -> Image.Image:
        """Create the base canvas with background"""
        if self.background_mode == "image" and self.background_image:
            canvas = self.background_image.copy()
        elif self.background_mode == "color":
            canvas = Image.new('RGB', (self.width, self.height), self.background_color)
        else:
            canvas = Image.new('RGB', (self.width, self.height), (255, 255, 255))
            
        return canvas

    def update_sensor_data(self, payload: Dict[str, Any]):
        if not self.initialized:
            return

        data = self._extract_sensor_data(payload)
        if data:
            self.sensor_data.update(data)
            self.last_update = datetime.now()
            self._refresh_display()
            print(f"[SensorDisplay] Updated sensor data: {len(data)} items")

    def update_config(self, payload: Dict[str, Any]):
        """Handle configuration updates including background settings - NO REFRESH"""
        print(f"[SensorDisplay] Config update received: {payload.get('type', 'unknown')}")
        
        # Handle background color in eink config
        if "eink" in payload and "background_color" in payload["eink"]:
            bg_color = payload["eink"]["background_color"]
            if isinstance(bg_color, list) and len(bg_color) == 3:
                self.set_background_color(tuple(bg_color))
                print(f"[SensorDisplay] Background color updated from config: {bg_color}")
        
        # Handle background image in eink config
        if "eink" in payload and "background_image" in payload["eink"]:
            bg_data = payload["eink"]["background_image"]
            opacity = payload["eink"].get("background_opacity", 1.0)
            
            if isinstance(bg_data, str):
                self.set_background_from_base64(bg_data, opacity)
                print("[SensorDisplay] Background image updated from config")
            elif isinstance(bg_data, bytes):
                self.set_background_image(bg_data, opacity)
                print("[SensorDisplay] Background image updated from config")

        # Handle top-level background settings (fallback)
        if "background_color" in payload:
            bg_color = payload["background_color"]
            if isinstance(bg_color, list) and len(bg_color) == 3:
                self.set_background_color(tuple(bg_color))
                print(f"[SensorDisplay] Background color updated from top-level config: {bg_color}")

        if "background_image" in payload:
            bg_data = payload["background_image"]
            opacity = payload.get("background_opacity", 1.0)
            
            if isinstance(bg_data, str):
                self.set_background_from_base64(bg_data, opacity)
                print("[SensorDisplay] Background image updated from top-level config")

    def show_status_screen(self):
        if not self.initialized:
            return
        image = self._create_base_canvas()
        draw = ImageDraw.Draw(image)
        y = 20
        draw.text((20, y), "System Status", font=self.font_big, fill=(0, 0, 0))
        y += 80
        status_info = [
            f"MAC: {self._get_mac_address()}",
            f"Uptime: {self._get_uptime()}",
            f"Last Update: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'None'}",
            f"Sensor Count: {len(self.sensor_data)}",
            f"Background: {self.background_mode}"
        ]
        for info in status_info:
            draw.text((20, y), info, font=self.font_medium, fill=(0, 0, 0))
            y += 40
        self._update_display(image)

    def _extract_sensor_data(self, payload: Dict[str, Any]) -> Dict[str, str]:
        result = {}
        target_screen = payload.get("screen", payload.get("screenId", ""))
        if target_screen and target_screen != "onboard_screen":
            print(f"[SensorDisplay] Ignoring payload for screen '{target_screen}'")
            return result
        if "sensors" in payload:
            for name, readings in payload["sensors"].items():
                if isinstance(readings, list) and readings:
                    reading = readings[0]
                    val = reading.get("Value", reading.get("value", "N/A"))
                    unit = reading.get("Unit", reading.get("unit", ""))
                    result[name] = f"{val}{unit}"
                elif isinstance(readings, dict):
                    val = readings.get("Value", readings.get("value", "N/A"))
                    unit = readings.get("Unit", readings.get("unit", ""))
                    result[name] = f"{val}{unit}"
                else:
                    result[name] = str(readings)
        elif "value" in payload:
            name = payload.get("name", payload.get("sensor", "Sensor"))
            result[name] = f"{payload.get('value')}{payload.get('unit', '')}"
        for field in ["temperature", "humidity", "pressure", "light", "co2"]:
            if field in payload:
                result[field.title()] = str(payload[field])
        return result

    def _refresh_display(self):
        image = self._create_base_canvas()
        draw = ImageDraw.Draw(image)
        self._draw_static_content(draw)
        self._draw_sensor_table(draw, self.sensor_data)
        self._update_display(image)

    def _draw_static_content(self, draw):
        LEFT = 10
        TOP = 8
        y = TOP
        
        # Add text outline for better visibility on background images
        text_color = (0, 0, 0)
        outline_color = (255, 255, 255)
        
        if self.background_mode == "image":
            # Draw outline for better visibility
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                draw.text((LEFT+dx, y+dy), "Junction", font=self.font_big, fill=outline_color)
        draw.text((LEFT, y), "Junction", font=self.font_big, fill=text_color)
        
        y += 80
        if self.background_mode == "image":
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                draw.text((LEFT+dx, y+dy), "Relay", font=self.font_big, fill=outline_color)
        draw.text((LEFT, y), "Relay", font=self.font_big, fill=(255, 0, 0))
        
        y += 80
        sub = "E-Paper Display Node"
        if self.background_mode == "image":
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                draw.text((LEFT+dx, y+dy), sub, font=self.font_medium, fill=(0,0,0))
        draw.text((LEFT, y), sub, font=self.font_medium, fill=(255, 255, 0))
        
        y += 50
        draw.line((0, y, self.width, y), fill=(0,0,0), width=2)

    def _draw_sensor_table(self, draw, data: Dict[str, str]):
        table_width = 280
        x = self.width - table_width - 10
        y = 10
        h = max(100, len(data) * 25 + 50)
        draw.rectangle([x, y, x + table_width, y + h], fill=(255,255,255), outline=(0,0,0))
        draw.text((x+5, y+5), "Live Sensor Data", font=self.font_small, fill=(0,0,0))
        draw.text((x + table_width - 100, y + 5), datetime.now().strftime("%H:%M"), font=self.font_small, fill=(0,0,0))
        draw.line((x+5, y+25, x+table_width-5, y+25), fill=(0,0,0))
        row_y = y + 33
        if not data:
            draw.text((x+8, row_y), "Waiting for data...", font=self.font_small, fill=(128,128,128))
        else:
            for name, value in data.items():
                if row_y + 22 > y + h - 5:
                    break
                draw.text((x + 8, row_y), f"{name}:", font=self.font_small, fill=(0,0,0))
                draw.text((x + table_width - 120, row_y), value, font=self.font_small, fill=(255,0,0))
                row_y += 22

    def _update_display(self, image):
        try:
            self.epd.display(self.epd.getbuffer(image))
        except Exception as e:
            print(f"[SensorDisplay] ERROR during display update: {e}")

    def _get_mac_address(self) -> str:
        try:
            import uuid
            return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
        except:
            return "00:00:00:00:00:00"

    def _get_uptime(self) -> str:
        try:
            with open('/proc/uptime', 'r') as f:
                seconds = float(f.readline().split()[0])
                return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
        except:
            return "Unknown"

    def shutdown(self):
        try:
            self.epd.sleep()
            print("[SensorDisplay] Display shutdown complete")
        except Exception as e:
            print(f"[SensorDisplay] ERROR during shutdown: {e}")