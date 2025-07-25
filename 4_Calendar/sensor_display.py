"""
Enhanced SensorDisplay with Calendar Layout Support
Adds TV Guide-style rendering for Sonarr episode data
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Tuple

def __init__(self, config):
    # ... existing init code ...
    
    # Add layout detection
    self.layout_type = "default"  # "default" or "calendar"
    self.calendar_config = {}

def update_config(self, payload: Dict[str, Any]):
    """Handle configuration updates including layout type detection"""
    print(f"[SensorDisplay] Config update received: {payload.get('type', 'unknown')}")
    
    # Detect layout type
    if "calendar" in payload:
        self.layout_type = "calendar"
        self.calendar_config = payload["calendar"]
        print("[SensorDisplay] Calendar layout detected")
    elif "lvgl_grid" in payload:
        self.layout_type = "default"
        print("[SensorDisplay] Grid layout detected")
    
    # ... existing background handling code ...

def _refresh_display(self):
    """Refresh display using appropriate layout renderer"""
    image = self._create_base_canvas()
    draw = ImageDraw.Draw(image)
    self._draw_static_content(draw)
    
    if self.layout_type == "calendar":
        self._render_calendar_layout(draw, self.sensor_data)
    else:
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