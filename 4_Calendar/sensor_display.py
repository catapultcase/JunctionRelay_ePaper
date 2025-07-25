"""
Sensor Display - Manages e-paper display updates
Handles real sensor data from Junction Relay protocol
Enhanced with background image support via config payloads
Added calendar layout support for TV Guide-style episode displays
Enhanced with timezone conversion and last updated display
"""

import os
import time
import tempfile
import base64
import io
import json
from datetime import datetime, timedelta
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
        self.font_tiny = None  # For last updated text

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
            self.font_tiny = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
        except Exception as e:
            print(f"[SensorDisplay] WARNING: Failed to load fonts: {e}")
            self.font_big = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()

    def _parse_utc_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Parse UTC datetime string and convert to local timezone"""
        if not datetime_str:
            return None
        
        try:
            # Handle both formats: "2025-08-08T01:00:00Z" and "01:00"
            if 'T' in datetime_str and datetime_str.endswith('Z'):
                # Full datetime with Z suffix (UTC)
                utc_dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
                # Convert UTC to local time
                utc_timestamp = utc_dt.timestamp()
                local_dt = datetime.fromtimestamp(utc_timestamp)
                return local_dt
            elif ':' in datetime_str and len(datetime_str) == 5:
                # Just time format "HH:MM" - assume it's already UTC and convert to local
                # We need a date to work with, so use today
                today = datetime.now().date()
                utc_time = datetime.strptime(f"{today} {datetime_str}", "%Y-%m-%d %H:%M")
                # Convert assuming this time is in UTC
                utc_timestamp = utc_time.replace(tzinfo=None).timestamp() - time.timezone
                local_dt = datetime.fromtimestamp(utc_timestamp)
                return local_dt
            else:
                print(f"[SensorDisplay] Unrecognized datetime format: {datetime_str}")
                return None
        except Exception as e:
            print(f"[SensorDisplay] Error parsing datetime '{datetime_str}': {e}")
            return None

    def _format_local_time(self, datetime_str: str) -> str:
        """Convert UTC time string to local time string"""
        local_dt = self._parse_utc_datetime(datetime_str)
        if local_dt:
            return local_dt.strftime("%H:%M")
        return datetime_str  # Fallback to original if parsing fails

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
        
        # Draw last updated in top right corner
        self._draw_last_updated(draw)
        
        if self.layout_type == "calendar":
            self._render_calendar_layout(draw, {})
        else:
            self._draw_static_content(draw)
            self._draw_sensor_table(draw, {})
        
        self._update_display(image)
        print("[SensorDisplay] Startup screen displayed")

    def _draw_last_updated(self, draw):
        """Draw last updated timestamp in top right corner"""
        if self.last_update:
            update_text = f"Last Updated: {self.last_update.strftime('%H:%M:%S')}"
        else:
            update_text = "Last Updated: Never"
        
        # Calculate text width to right-align
        try:
            if hasattr(self.font_tiny, 'getbbox'):
                bbox = self.font_tiny.getbbox(update_text)
                text_width = bbox[2] - bbox[0]
            elif hasattr(self.font_tiny, 'getsize'):
                text_width = self.font_tiny.getsize(update_text)[0]
            else:
                text_width = len(update_text) * 7
        except:
            text_width = len(update_text) * 7
        
        # Position in top right corner with small margin
        x = self.width - text_width - 5
        y = 3
        
        # Draw with subtle color
        draw.text((x, y), update_text, font=self.font_tiny, fill=(128, 128, 128))

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
        
        # Draw last updated in top right corner
        self._draw_last_updated(draw)
        
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
        print(f"[DEBUG] _refresh_display called, layout_type='{self.layout_type}'")
        
        image = self._create_base_canvas()
        draw = ImageDraw.Draw(image)
        
        # Always draw last updated in top right corner
        self._draw_last_updated(draw)
        
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
        """Render TV Guide style calendar layout - proper 2-column table per day"""
        print(f"[DEBUG] Calendar render called with {len(sensor_data)} sensors")
        
        # Count day sensors to determine layout
        column_count, day_sensor_keys = self._count_day_sensors(sensor_data)
        print(f"[DEBUG] Column count: {column_count}, Keys: {day_sensor_keys}")
        
        if column_count == 0:
            # No day sensors found, show message
            draw.text((50, 100), "No episode data available", font=self.font_medium, fill=(0, 0, 0))
            return
        
        # Full screen layout - use entire display with proper spacing
        # Account for last updated text at top (reserve 20px)
        header_height = 45
        content_start_y = 25  # Start below the "Last Updated" text
        column_separator_width = 30  # Wider separation between day columns
        
        # Calculate day column width with separator space
        total_separator_width = (column_count - 1) * column_separator_width
        available_width = self.width - 20 - total_separator_width  # 10px margins + separator space
        day_column_width = available_width // column_count
        
        # Within each day column: TIME | TITLE structure
        time_column_width = 50   # Fixed width for time
        title_column_width = day_column_width - time_column_width - 10  # Remaining for titles
        
        print(f"[DEBUG] Display: {self.width}x{self.height}, Day column: {day_column_width}, Time: {time_column_width}, Title: {title_column_width}")
        
        # Column headers mapping with date only for Today
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        header_map = {
            "episodes-yesterday": "Yesterday",
            "episodes-today": f"Today ({today.strftime('%-m/%-d/%Y')})", 
            "episodes-tomorrow": "Tomorrow"
        }
        
        # Render each day column
        for col_index, sensor_key in enumerate(day_sensor_keys):
            day_x_start = 10 + (col_index * (day_column_width + column_separator_width))
            print(f"[DEBUG] Day column {col_index} ({sensor_key}) at x={day_x_start}")
            
            # Draw day header
            header_text = header_map.get(sensor_key, sensor_key)
            draw.text((day_x_start + 5, content_start_y), header_text, font=self.font_medium, fill=(0, 0, 0))
            
            # Draw day column separator line (except for first column)
            if col_index > 0:
                line_x = day_x_start - (column_separator_width // 2)
                draw.line((line_x, content_start_y, line_x, self.height - 10), fill=(128, 128, 128), width=1)
            
            # Draw header underline
            draw.line((day_x_start + 5, content_start_y + 35, day_x_start + day_column_width - 10, content_start_y + 35), 
                     fill=(0, 0, 0), width=1)
            
            # Parse and render episodes for this day (start right after header)
            episodes_start_y = content_start_y + header_height + 5
            episodes_y = episodes_start_y
            
            if sensor_key in sensor_data:
                episodes = self._parse_episode_json(sensor_data[sensor_key])
                print(f"[DEBUG] Rendering {len(episodes)} episodes for {sensor_key}")
                
                if not episodes:
                    # Empty day
                    title_x = day_x_start + 8 + time_column_width + 15
                    draw.text((title_x, episodes_y), "No episodes", 
                             font=self.font_small, fill=(128, 128, 128))
                else:
                    # Render each episode in table rows
                    for episode_idx, episode in enumerate(episodes):
                        row_height = 44  # Fixed height per episode row (for 2 lines max)
                        
                        if episodes_y + row_height > self.height - 10:  # Prevent overflow
                            print(f"[DEBUG] Stopping at episode {episode_idx} due to overflow at y={episodes_y}")
                            break
                        
                        # Extract episode info
                        series = episode.get('series', 'Unknown Show')
                        air_time = episode.get('airTime', '')
                        
                        # Convert UTC time to local time
                        if air_time:
                            local_time = self._format_local_time(air_time)
                            print(f"[DEBUG] Converted time {air_time} -> {local_time}")
                        else:
                            local_time = air_time
                        
                        # Clean up series name (remove episode details after " - ")
                        if ' - ' in series:
                            show_name = series.split(' - ')[0]
                            episode_part = series.split(' - ', 1)[1]
                            display_text = f"{show_name} - {episode_part}"
                        else:
                            display_text = series
                        
                        # Calculate positions with more padding between columns
                        time_x = day_x_start + 8  # 3px extra padding from left edge
                        title_x = day_x_start + 8 + time_column_width + 15  # 15px gap between columns (was 8px)
                        
                        # Render TIME column (fixed position, single line) - use local time
                        if local_time:
                            draw.text((time_x, episodes_y + 2), local_time, font=self.font_small, fill=(0, 0, 0))  # +2px top padding
                        
                        # Render TITLE column with wrapping constrained to this row
                        self._draw_wrapped_text_in_row(
                            draw, display_text, title_x, episodes_y + 2, 
                            title_column_width - 23, row_height - 4, self.font_small, (0, 0, 0)  # -23px for padding (was -16px)
                        )
                        
                        episodes_y += row_height  # Move to next row
            else:
                # Sensor not found
                print(f"[DEBUG] Sensor {sensor_key} not found in data")
                title_x = day_x_start + 8 + time_column_width + 15
                draw.text((title_x, episodes_y), "No data", 
                         font=self.font_small, fill=(128, 128, 128))
        
        print("[DEBUG] Calendar rendering complete")

    def _draw_wrapped_text_in_row(self, draw, text: str, x: int, y: int, max_width: int, row_height: int, font, color) -> None:
        """Draw text with wrapping constrained to a specific row height"""
        words = text.split(' ')
        lines = []
        current_line = []
        line_height = 20
        max_lines = row_height // line_height  # How many lines fit in this row
        
        # Build lines that fit within max_width
        for word in words:
            test_line = ' '.join(current_line + [word])
            
            try:
                # Try to get actual text width
                if hasattr(font, 'getbbox'):
                    bbox = font.getbbox(test_line)
                    text_width = bbox[2] - bbox[0]
                elif hasattr(font, 'getsize'):
                    text_width = font.getsize(test_line)[0]
                else:
                    text_width = len(test_line) * 7
            except:
                text_width = len(test_line) * 7
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word too long, truncate it
                    truncated_word = word
                    while len(truncated_word) > 3:
                        try:
                            if hasattr(font, 'getbbox'):
                                bbox = font.getbbox(truncated_word + "...")
                                test_width = bbox[2] - bbox[0]
                            elif hasattr(font, 'getsize'):
                                test_width = font.getsize(truncated_word + "...")[0]
                            else:
                                test_width = len(truncated_word + "...") * 7
                        except:
                            test_width = len(truncated_word + "...") * 7
                        
                        if test_width <= max_width:
                            break
                        truncated_word = truncated_word[:-1]
                    
                    lines.append(truncated_word + "..." if len(truncated_word) < len(word) else word)
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to what fits in the row
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            # Add ellipsis to last line if truncated
            if len(lines) > 0 and max_lines > 0:
                last_line = lines[-1]
                if len(last_line) > 3:
                    lines[-1] = last_line[:-3] + "..."
        
        # Draw each line within the row
        current_y = y
        for line in lines:
            if current_y + line_height <= y + row_height:  # Ensure we stay within row bounds
                draw.text((x, current_y), line, font=font, fill=color)
                current_y += line_height
            else:
                break  # Stop if we would exceed row height
        
        print(f"[DEBUG] Row text '{text[:15]}...' -> {len(lines)} lines in {row_height}px row")

    def _draw_wrapped_text(self, draw, text: str, x: int, y: int, max_width: int, font, color) -> int:
        """Draw text with proper word wrapping using actual font metrics"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        # Build lines that fit within max_width using actual text measurement
        for word in words:
            test_line = ' '.join(current_line + [word])
            
            try:
                # Try to get actual text width (PIL methods vary by version)
                if hasattr(font, 'getbbox'):
                    bbox = font.getbbox(test_line)
                    text_width = bbox[2] - bbox[0]
                elif hasattr(font, 'getsize'):
                    text_width = font.getsize(test_line)[0]
                else:
                    # Fallback to character estimation
                    text_width = len(test_line) * 7
            except:
                # Fallback to character estimation if font methods fail
                text_width = len(test_line) * 7
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word too long, need to truncate
                    truncated_word = word
                    while True:
                        try:
                            if hasattr(font, 'getbbox'):
                                bbox = font.getbbox(truncated_word + "...")
                                test_width = bbox[2] - bbox[0]
                            elif hasattr(font, 'getsize'):
                                test_width = font.getsize(truncated_word + "...")[0]
                            else:
                                test_width = len(truncated_word) * 7
                        except:
                            test_width = len(truncated_word) * 7
                        
                        if test_width <= max_width or len(truncated_word) <= 3:
                            break
                        truncated_word = truncated_word[:-1]
                    
                    lines.append(truncated_word + "..." if len(truncated_word) < len(word) else word)
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit to 2 lines maximum
        if len(lines) > 2:
            lines = lines[:2]
            # Ensure second line fits with ellipsis if needed
            if len(lines) == 2:
                second_line = lines[1]
                try:
                    if hasattr(font, 'getbbox'):
                        bbox = font.getbbox(second_line)
                        text_width = bbox[2] - bbox[0]
                    elif hasattr(font, 'getsize'):
                        text_width = font.getsize(second_line)[0]
                    else:
                        text_width = len(second_line) * 7
                except:
                    text_width = len(second_line) * 7
                
                if text_width > max_width:
                    # Truncate second line
                    while len(second_line) > 3:
                        try:
                            if hasattr(font, 'getbbox'):
                                bbox = font.getbbox(second_line[:-3] + "...")
                                test_width = bbox[2] - bbox[0]
                            elif hasattr(font, 'getsize'):
                                test_width = font.getsize(second_line[:-3] + "...")[0]
                            else:
                                test_width = len(second_line[:-3] + "