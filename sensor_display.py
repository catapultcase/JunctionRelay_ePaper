"""
Sensor Display - Manages e-paper display updates
Handles real sensor data from Junction Relay protocol
"""

import sys
import os
import time
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional

# Import our safe wrapper instead of direct waveshare import
from epaper_wrapper import EPaperDisplay

class SensorDisplay:
    """Manages e-paper display for sensor data visualization"""
    
    def __init__(self, config):
        self.config = config
        self.display = None
        self.width = 792
        self.height = 272
        self.initialized = False
        
        # Current sensor data
        self.sensor_data = {}
        self.last_update = None
        
        # Fonts
        self.font_big = None
        self.font_medium = None  
        self.font_small = None
        
    def initialize(self) -> bool:
        """Initialize the e-paper display"""
        try:
            # Use our safe wrapper
            self.display = EPaperDisplay()
            
            if self.display.initialize():
                self.width, self.height = self.display.get_dimensions()
                
                # Load fonts
                self._load_fonts()
                
                self.initialized = True
                
                if self.display.is_hardware:
                    print(f"[SensorDisplay] Real e-paper display initialized: {self.width}x{self.height}")
                else:
                    print(f"[SensorDisplay] Mock display initialized: {self.width}x{self.height}")
                    
                return True
            else:
                print("[SensorDisplay] Failed to initialize display")
                return False
                
        except Exception as e:
            print(f"[SensorDisplay] ERROR: Initialization failed: {e}")
            return False
            
    def _load_fonts(self):
        """Load display fonts"""
        try:
            self.font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
            self.font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
            self.font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except Exception as e:
            print(f"[SensorDisplay] WARNING: Could not load fonts: {e}")
            # Use default font
            self.font_big = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            
    def show_startup_screen(self):
        """Display startup screen"""
        if not self.initialized:
            return
            
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Draw Junction Relay branding
        self._draw_static_content(draw)
        
        # Show initial sensor table (empty)
        self._draw_sensor_table(draw, {})
        
        self._update_display(image)
        print("[SensorDisplay] Startup screen displayed")
        
    def update_sensor_data(self, payload: Dict[str, Any]):
        """Update display with new sensor data"""
        if not self.initialized:
            return
            
        # Extract sensor values from payload
        sensor_data = self._extract_sensor_data(payload)
        if sensor_data:
            self.sensor_data.update(sensor_data)
            self.last_update = datetime.now()
            self._refresh_display()
            print(f"[SensorDisplay] Updated sensor data: {len(sensor_data)} values")
            
    def update_config(self, payload: Dict[str, Any]):
        """Update display configuration"""
        print(f"[SensorDisplay] Config update received: {payload.get('type', 'unknown')}")
        # Could handle display settings, themes, etc.
        
    def show_status_screen(self):
        """Show system status screen"""
        if not self.initialized:
            return
            
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Status info
        y = 20
        draw.text((20, y), "System Status", font=self.font_big, fill=(0, 0, 0))
        y += 80
        
        status_info = [
            f"MAC: {self._get_mac_address()}",
            f"Uptime: {self._get_uptime()}",
            f"Last Update: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'None'}",
            f"Sensor Count: {len(self.sensor_data)}"
        ]
        
        for info in status_info:
            draw.text((20, y), info, font=self.font_medium, fill=(0, 0, 0))
            y += 40
            
        self._update_display(image)
        
    def _extract_sensor_data(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Extract sensor data from Junction Relay payload"""
        sensor_data = {}
        
        # Check if this payload is targeted at our screen
        target_screen = payload.get("screen", payload.get("screenId", ""))
        if target_screen and target_screen != "onboard_screen":
            print(f"[SensorDisplay] Payload targeted at '{target_screen}', ignoring (we are 'onboard_screen')")
            return {}
        
        # Handle your backend's actual format: 
        # {'sensors': {'rate_tester': [{'Value': '542', 'Unit': '%'}]}}
        if "sensors" in payload:
            sensors_dict = payload["sensors"]
            
            # Handle your specific format where sensors is a dict of sensor_name -> list of readings
            for sensor_name, readings_list in sensors_dict.items():
                if isinstance(readings_list, list) and len(readings_list) > 0:
                    # Take the first (or latest) reading
                    reading = readings_list[0]
                    if isinstance(reading, dict):
                        value = reading.get("Value", reading.get("value", "N/A"))
                        unit = reading.get("Unit", reading.get("unit", ""))
                        sensor_data[sensor_name] = f"{value}{unit}"
                    else:
                        sensor_data[sensor_name] = str(reading)
                elif isinstance(readings_list, dict):
                    # Handle case where it's a single reading dict
                    value = readings_list.get("Value", readings_list.get("value", "N/A"))
                    unit = readings_list.get("Unit", readings_list.get("unit", ""))
                    sensor_data[sensor_name] = f"{value}{unit}"
                else:
                    sensor_data[sensor_name] = str(readings_list)
                    
        # Handle legacy format if needed
        elif "value" in payload:
            name = payload.get("name", payload.get("sensor", "Sensor"))
            value = payload.get("value")
            unit = payload.get("unit", "")
            sensor_data[name] = f"{value}{unit}"
            
        # Handle common sensor fields at root level
        common_fields = ["temperature", "humidity", "pressure", "light", "co2"]
        for field in common_fields:
            if field in payload:
                sensor_data[field.title()] = str(payload[field])
                
        return sensor_data
        
    def _refresh_display(self):
        """Refresh the entire display with current data"""
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Draw static content
        self._draw_static_content(draw)
        
        # Draw sensor table with current data
        self._draw_sensor_table(draw, self.sensor_data)
        
        self._update_display(image)
        
    def _draw_static_content(self, draw):
        """Draw static Junction Relay branding"""
        LEFT = 10
        TOP = 8
        
        y = TOP
        
        # Header
        draw.text((LEFT, y), "Junction", font=self.font_big, fill=(0, 0, 0))
        y += 80
        draw.text((LEFT, y), "Relay", font=self.font_big, fill=(255, 0, 0))
        y += 80
        
        # Subheading with outline effect
        subheading = "E-Paper Display Node"
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((LEFT + dx, y + dy), subheading, font=self.font_medium, fill=(0, 0, 0))
        draw.text((LEFT, y), subheading, font=self.font_medium, fill=(255, 255, 0))
        y += 50
        
        # Divider line
        draw.line((0, y, self.width, y), fill=(0, 0, 0), width=2)
        
    def _draw_sensor_table(self, draw, sensor_data: Dict[str, str]):
        """Draw sensor data table in top-right corner"""
        # Table dimensions
        table_width = 280
        table_x = self.width - table_width - 10
        table_y = 10
        
        # Calculate table height based on number of sensors
        num_sensors = len(sensor_data) if sensor_data else 1
        table_height = num_sensors * 25 + 50  # 25px per sensor + header space
        
        # Ensure minimum height
        if table_height < 100:
            table_height = 100
        
        # Draw table background and border
        draw.rectangle([table_x, table_y, table_x + table_width, table_y + table_height],
                      fill=(255, 255, 255), outline=(0, 0, 0), width=1)
        
        # Table header
        header_y = table_y + 5
        draw.text((table_x + 5, header_y), "Live Sensor Data", font=self.font_small, fill=(0, 0, 0))
        draw.text((table_x + table_width - 100, header_y), datetime.now().strftime("%H:%M"),
                 font=self.font_small, fill=(0, 0, 0))
        
        # Header divider line
        line_y = header_y + 20
        draw.line((table_x + 5, line_y, table_x + table_width - 5, line_y),
                 fill=(0, 0, 0), width=1)
        
        # Sensor data rows
        row_y = line_y + 8
        
        if sensor_data:
            for sensor_name, sensor_value in sensor_data.items():
                # Check if we have room for this row
                if row_y + 22 > table_y + table_height - 5:
                    break  # Don't overflow the table
                    
                # Draw sensor name and value
                draw.text((table_x + 8, row_y), f"{sensor_name}:", font=self.font_small, fill=(0, 0, 0))
                draw.text((table_x + table_width - 120, row_y), str(sensor_value), font=self.font_small, fill=(255, 0, 0))
                row_y += 22
        else:
            # No sensor data available
            draw.text((table_x + 8, row_y), "Waiting for data...", font=self.font_small, fill=(128, 128, 128))
            
    def _update_display(self, image):
        """Update the physical display"""
        if not self.display:
            return
            
        try:
            if self.display.is_hardware:
                # Real hardware update
                self.display.display(image)
            else:
                # Mock display - save image for testing
                temp_path = tempfile.gettempdir()
                image_path = os.path.join(temp_path, "epaper_display.png")
                image.save(image_path)
                print(f"[SensorDisplay] Mock display updated - saved to {image_path}")
        except Exception as e:
            print(f"[SensorDisplay] ERROR: Display update failed: {e}")
            
    def _get_mac_address(self) -> str:
        """Get system MAC address"""
        try:
            import uuid
            return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                           for ele in range(0,8*6,8)][::-1])
        except:
            return "00:00:00:00:00:00"
            
    def _get_uptime(self) -> str:
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"
        except:
            return "Unknown"
            
    def shutdown(self):
        """Shutdown the display"""
        if self.display:
            try:
                self.display.sleep()
                print("[SensorDisplay] Display shutdown complete")
            except Exception as e:
                print(f"[SensorDisplay] ERROR during shutdown: {e}")