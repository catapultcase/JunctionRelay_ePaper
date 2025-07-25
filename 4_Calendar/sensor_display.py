"""
Sensor Display - Manages e-paper display updates
Handles real sensor data from Junction Relay protocol
Enhanced with background image support via config payloads
Added calendar layout support for TV Guide-style episode displays
"""

import os
import time
import tempfile
import base64
import io
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
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

        # Layout detection
        self.layout_type = "default"  # "default" or "calendar"
        self.calendar_config = {}

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
        
        if self.layout_type == "calendar":
            self._render_calendar_layout(draw, {})
        else:
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
        """Handle configuration updates including background settings and layout detection"""
        print(f"[SensorDisplay] Config update received: {payload.get('type', 'unknown')}")
        
        # Detect layout type
        if "calendar" in payload:
            self.layout_type = "calendar"
            self.calendar_config = payload["calendar"]
            print("[SensorDisplay] Calendar layout detected")
        elif "lvgl_grid" in payload:
            self.layout_type = "default"
            print("[SensorDisplay] Grid layout detected")
        
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
            f"Background: {self.background_mode}",
            f"Layout: {self.layout_type}"
        ]
        for info in status_info:
            draw.text((20, y), info, font=self.font_medium, fill=(0, 0, 0))
            y += 40
        self._update_display(image)

    def _extract_sensor_data(self, payload: Dict[str, Any]) -> Dict[str, str]:
        result = {}
        target_screen = payload.get("screen", payload.get("screenId", ""))
        if target_screen and target_screen != "onboard_screen" and target_screen != "onboard":
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
        """Refresh display using appropriate layout renderer"""
        image = self._create_base_canvas()
        draw = ImageDraw.Draw(image)
        
        if self.layout_type == "calendar":
            self._render_calendar_layout(draw, self.sensor_data)
        else:
            self._draw_static_content(draw)
            self._draw_sensor_table(draw, self.sensor_data)
        
        self._update_display(image)

    def _count_day_sensors(self, sensor_data: Dict[str, str]) -> Tuple[int, List[str]]:
        """Count day-specific sensors and return column count and sensor keys"""
        day_sensors = []
        
        # Check for specific day sensors in order: yesterday, today, tomorrow
        if "episodes-yesterday" in sensor_data:
            day_sensors.append("episodes-yesterday")
        if "episodes-today" in sensor_data:
            day_sensors.append("episodes-today") 
        if "episodes-tomorrow" in sensor_data:
            day_sensors.append("episodes-tomorrow")
        
        return len(day_sensors), day_sensors

    def _parse_episode_json(self, json_string: str) -> List[Dict[str, Any]]:
        """Parse episode JSON data and return list of episodes"""
        try:
            # Remove the unit suffix if present (e.g., "Episodes JSON")
            if json_string.endswith("Episodes JSON"):
                json_string = json_string[:-13].strip()
            
            episodes = json.loads(json_string)
            if isinstance(episodes, list):
                return episodes
            return []
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[SensorDisplay] Error parsing episode JSON: {e}")
            return []

    def _render_calendar_layout(self, draw, sensor_data: Dict[str, str]):
        """Render TV Guide style calendar layout"""
        # Count day sensors to determine layout
        column_count, day_sensor_keys = self._count_day_sensors(sensor_data)
        
        if column_count == 0:
            # No day sensors found, show message
            draw.text((20, 200), "No episode data available", font=self.font_medium, fill=(128, 128, 128))
            return
        
        # Calculate layout dimensions
        content_start_y = 200  # Start below static content
        content_height = self.height - content_start_y - 20
        column_width = (self.width - 40) // column_count
        
        # Column headers mapping
        header_map = {
            "episodes-yesterday": "Yesterday",
            "episodes-today": "Today", 
            "episodes-tomorrow": "Tomorrow"
        }
        
        # Render each column
        for col_index, sensor_key in enumerate(day_sensor_keys):
            x_start = 20 + (col_index * column_width)
            
            # Draw column header
            header_text = header_map.get(sensor_key, sensor_key)
            draw.text((x_start + 5, content_start_y), header_text, font=self.font_medium, fill=(0, 0, 0))
            
            # Draw column separator line
            if col_index > 0:
                line_x = x_start - 1
                draw.line((line_x, content_start_y, line_x, self.height - 20), fill=(128, 128, 128), width=1)
            
            # Draw header underline
            draw.line((x_start + 5, content_start_y + 35, x_start + column_width - 10, content_start_y + 35), 
                     fill=(0, 0, 0), width=1)
            
            # Parse and render episodes for this day
            episodes_y = content_start_y + 45
            
            if sensor_key in sensor_data:
                episodes = self._parse_episode_json(sensor_data[sensor_key])
                
                if not episodes:
                    # Empty day
                    draw.text((x_start + 5, episodes_y), "No episodes", 
                             font=self.font_small, fill=(128, 128, 128))
                else:
                    # Render each episode
                    for episode in episodes:
                        if episodes_y + 20 > self.height - 25:  # Prevent overflow
                            break
                        
                        # Extract episode info
                        series = episode.get('series', 'Unknown Show')
                        air_time = episode.get('airTime', '')
                        
                        # Clean up series name (remove episode details after " - ")
                        if ' - ' in series:
                            show_name = series.split(' - ')[0]
                            episode_part = series.split(' - ', 1)[1]
                            # Truncate episode part if too long
                            if len(episode_part) > 15:
                                episode_part = episode_part[:12] + "..."
                            display_text = f"{show_name} - {episode_part}"
                        else:
                            display_text = series
                        
                        # Truncate if too long for column
                        max_chars = (column_width - 15) // 6  # Rough character width estimation
                        if len(display_text) > max_chars:
                            display_text = display_text[:max_chars-3] + "..."
                        
                        # Draw time and show
                        if air_time:
                            time_text = f"{air_time} {display_text}"
                        else:
                            time_text = display_text
                        
                        draw.text((x_start + 5, episodes_y), time_text, 
                                 font=self.font_small, fill=(0, 0, 0))
                        
                        episodes_y += 18  # Line spacing
            else:
                # Sensor not found
                draw.text((x_start + 5, episodes_y), "No data", 
                         font=self.font_small, fill=(128, 128, 128))
        
        # Draw bottom border
        draw.line((20, self.height - 20, self.width - 20, self.height - 20), 
                 fill=(0, 0, 0), width=1)

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