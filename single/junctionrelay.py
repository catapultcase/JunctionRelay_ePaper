#!/usr/bin/python3
# -*- coding:utf-8 -*-

import sys
import os
import time
import traceback
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Add correct driver path
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd5in79g

def generate_sensor_data():
    """Generate fake sensor data"""
    return {
        "Temp": f"{random.uniform(18.0, 28.0):.1f}°C",
        "Humidity": f"{random.uniform(30.0, 70.0):.1f}%",
        "Pressure": f"{random.uniform(995.0, 1025.0):.0f} hPa",
        "Light": f"{random.uniform(100, 1000):.0f} lux",
        "CO2": f"{random.uniform(400, 800):.0f} ppm"
    }

def draw_sensor_table(draw, font_small, sensor_data, table_x, table_y, table_width):
    """Draw the sensor data table"""
    # Clear the sensor table area first (white rectangle)
    table_height = len(sensor_data) * 25 + 40  # rough estimate
    draw.rectangle([table_x, table_y, table_x + table_width, table_y + table_height], 
                   fill=(255, 255, 255), outline=(0, 0, 0), width=1)
    
    # Table header
    header_y = table_y + 5
    draw.text((table_x + 5, header_y), "Sensor Data", font=font_small, fill=(0, 0, 0))
    draw.text((table_x + table_width - 100, header_y), datetime.now().strftime("%H:%M"), 
              font=font_small, fill=(0, 0, 0))
    
    # Divider line
    line_y = header_y + 20
    draw.line((table_x + 5, line_y, table_x + table_width - 5, line_y), 
              fill=(0, 0, 0), width=1)
    
    # Sensor data rows
    row_y = line_y + 8
    for sensor, value in sensor_data.items():
        draw.text((table_x + 8, row_y), sensor + ":", font=font_small, fill=(0, 0, 0))
        draw.text((table_x + table_width - 120, row_y), value, font=font_small, fill=(255, 0, 0))  # Moved further left
        row_y += 22
    
    return table_height

def draw_static_content(draw, width, height, font_big, font_medium, font_small):
    """Draw the static content that doesn't change"""
    LEFT = 10
    TOP = 8
    LINE_SPACING = 12
    
    # Calculate line heights
    big_h = font_big.getbbox("Ag")[3]
    medium_h = font_medium.getbbox("Ag")[3]
    small_h = font_small.getbbox("Ag")[3]
    
    y = TOP
    
    # Draw header text
    draw.text((LEFT, y), "Junction", font=font_big, fill=(0, 0, 0))  # Black
    y += big_h + LINE_SPACING
    draw.text((LEFT, y), "Relay", font=font_big, fill=(255, 0, 0))   # Red
    y += big_h + LINE_SPACING
    
    # Draw outlined yellow subheading
    subheading = "Device Orchestration Platform"
    x = LEFT
    
    # Shadow offsets around the yellow text
    shadow_offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dx, dy in shadow_offsets:
        draw.text((x + dx, y + dy), subheading, font=font_medium, fill=(0, 0, 0))  # shadow/outline
    
    draw.text((x, y), subheading, font=font_medium, fill=(255, 255, 0))  # foreground
    y += medium_h + LINE_SPACING
    
    # Divider
    draw.line((0, y, width, y), fill=(0, 0, 0), width=2)
    y += LINE_SPACING
    
    # Feature list
    capabilities = [
        ("WiFi & ESP-NOW support", (0, 0, 0)),
        ("Realtime sensor payloads", (255, 0, 0)),
        ("OLED, Matrix, NeoPixel output", (255, 255, 0)),
        ("Cloud + Local control", (0, 0, 0)),
        ("Push notifications", (255, 0, 0)),
        ("Open-core & modular", (0, 0, 0)),
    ]
    
    for text, color in capabilities:
        if y + small_h + 8 > height:
            break  # don't overflow
        draw.text((LEFT, y), f"• {text}", font=font_small, fill=color)
        y += small_h + 6

try:
    print("[INFO] Initializing display...")
    epd = epd5in79g.EPD()
    epd.init()

    print("[INFO] Clearing display...")
    epd.Clear()

    width, height = epd.width, epd.height
    print(f"[INFO] Display size: {width}x{height}")

    # Load fonts
    font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
    font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 32)
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)

    # Create main canvas and draw static content
    image = Image.new('RGB', (width, height), (255, 255, 255))  # white background
    draw = ImageDraw.Draw(image)
    
    # Draw static content once
    draw_static_content(draw, width, height, font_big, font_medium, font_small)
    
    # Define sensor table area (top right corner)
    table_width = 280  # Increased from 200 to 280
    table_x = width - table_width - 10
    table_y = 10
    
    # Initial sensor data and table
    sensor_data = generate_sensor_data()
    table_height = draw_sensor_table(draw, font_small, sensor_data, table_x, table_y, table_width)
    
    print("[INFO] Displaying initial image...")
    epd.display(epd.getbuffer(image))
    
    # Try to initialize partial update mode
    partial_update_available = False
    try:
        # Check if the display supports partial updates
        if hasattr(epd, 'PART_UPDATE') and hasattr(epd, 'displayPartial'):
            print("[INFO] Initializing partial update mode...")
            epd.init(epd.PART_UPDATE)
            partial_update_available = True
            print("[INFO] Partial update mode enabled!")
        else:
            print("[INFO] Partial update not available, using optimized full refreshes...")
    except Exception as e:
        print(f"[INFO] Partial update initialization failed: {e}")
        print("[INFO] Falling back to optimized full refreshes...")
    
    print(f"[INFO] Starting update loop (Partial updates: {partial_update_available})...")
    
    # Main loop - update sensor data every minute
    update_count = 0
    try:
        while True:
            print(f"[INFO] Waiting 60 seconds for next update... (Update #{update_count + 1})")
            time.sleep(60)  # Wait 1 minute
            
            # Generate new sensor data
            sensor_data = generate_sensor_data()
            
            if partial_update_available:
                # Use partial update
                # Create a new image with updated sensor data
                partial_image = Image.new('RGB', (width, height), (255, 255, 255))
                partial_draw = ImageDraw.Draw(partial_image)
                
                # Redraw the static content (needed for partial update reference)
                draw_static_content(partial_draw, width, height, font_big, font_medium, font_small)
                
                # Draw updated sensor table
                draw_sensor_table(partial_draw, font_small, sensor_data, table_x, table_y, table_width)
                
                print(f"[INFO] Partial update #{update_count + 1} - refreshing sensor data...")
                print(f"[INFO] Current sensor readings: {', '.join([f'{k}={v}' for k, v in sensor_data.items()])}")
                
                epd.displayPartial(epd.getbuffer(partial_image))
                
                # Every 10 partial updates, do a full refresh to prevent ghosting
                if update_count % 10 == 0 and update_count > 0:
                    print("[INFO] Performing full refresh to clear ghosting...")
                    epd.init()  # Re-initialize for full update
                    epd.display(epd.getbuffer(partial_image))
                    epd.init(epd.PART_UPDATE)  # Switch back to partial update mode
                    
            else:
                # Use full refresh
                # Create a new image with updated sensor data
                new_image = Image.new('RGB', (width, height), (255, 255, 255))
                new_draw = ImageDraw.Draw(new_image)
                
                # Redraw the static content
                draw_static_content(new_draw, width, height, font_big, font_medium, font_small)
                
                # Draw updated sensor table
                draw_sensor_table(new_draw, font_small, sensor_data, table_x, table_y, table_width)
                
                print(f"[INFO] Full refresh #{update_count + 1} - updating display...")
                print(f"[INFO] Current sensor readings: {', '.join([f'{k}={v}' for k, v in sensor_data.items()])}")
                
                # Display the updated image
                epd.display(epd.getbuffer(new_image))
                
                # Every 5 updates (5 minutes), do a clear and refresh to prevent any potential issues
                if update_count % 5 == 0 and update_count > 0:
                    print("[INFO] Performing maintenance clear and refresh...")
                    epd.Clear()
                    time.sleep(2)  # Brief pause after clear
                    epd.display(epd.getbuffer(new_image))
            
            update_count += 1
                
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        
    print("[INFO] Putting display to sleep...")
    epd.sleep()
    print("[SUCCESS] Display sleeping.")

except Exception as e:
    print("[ERROR] Exception occurred:")
    traceback.print_exc()
    try:
        epd.sleep()
    except:
        pass