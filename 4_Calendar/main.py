#!/usr/bin/env python3
"""
E-Paper Junction Relay - Main Entry Point
Replicates Junction Relay architecture for e-paper displays
"""

import sys
import os
import signal
import time
from threading import Thread

# Add project directory to path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from stream_processor import StreamProcessor
from http_endpoints import HTTPEndpoints
from sensor_display import SensorDisplay
from device_config import DeviceConfig
from utils import setup_logging, get_mac_address

class EPaperJunctionRelay:
    def __init__(self):
        self.config = DeviceConfig()
        self.display = SensorDisplay(self.config)
        self.stream_processor = None
        self.http_server = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def initialize(self):
        """Initialize all components"""
        print("[Main] Initializing E-Paper Junction Relay...")
        
        # Initialize display
        if not self.display.initialize():
            print("[Main] ERROR: Failed to initialize display")
            return False
            
        # Initialize stream processor with callbacks
        self.stream_processor = StreamProcessor(
            display_callback=self.handle_display_data,
            system_callback=self.handle_system_data
        )
        
        # Initialize HTTP server
        self.http_server = HTTPEndpoints(
            stream_processor=self.stream_processor,
            config=self.config
        )
        
        print(f"[Main] Device MAC: {get_mac_address()}")
        print(f"[Main] Display Size: {self.display.width}x{self.display.height}")
        print("[Main] ✅ Initialization complete")
        return True
        
    def start(self):
        """Start the service"""
        if not self.initialize():
            return False
            
        self.running = True
        
        # Start HTTP server in background thread
        server_thread = Thread(target=self.http_server.start_server, daemon=True)
        server_thread.start()
        
        # Show initial display
        self.display.show_startup_screen()
        
        print("[Main] 🚀 E-Paper Junction Relay started")
        print("[Main] HTTP server running on port 80")
        print("[Main] Endpoints:")
        print("[Main]   POST /api/data - Main data ingestion")
        print("[Main]   GET  /api/device/info - Device information")
        print("[Main]   GET  /api/system/stats - System statistics")
        print("[Main] Press Ctrl+C to stop")
        
        # Main loop
        try:
            while self.running:
                time.sleep(1)
                # Could add periodic tasks here
                
        except KeyboardInterrupt:
            pass
            
        self.shutdown()
        return True
        
    def handle_display_data(self, data_type: str, payload: dict):
        """Handle data destined for display update"""
        if data_type == "sensor":
            self.display.update_sensor_data(payload)
        elif data_type == "config":
            self.display.update_config(payload)
        else:
            print(f"[Main] Unknown display data type: {data_type}")
            
    def handle_system_data(self, data_type: str, payload: dict):
        """Handle system-level data"""
        if data_type == "device_info":
            print("[Main] Device info request received")
        elif data_type == "preferences":
            print("[Main] Preferences update received")
        elif data_type == "system_command":
            self.handle_system_command(payload)
        else:
            print(f"[Main] Unknown system data type: {data_type}")
            
    def handle_system_command(self, payload: dict):
        """Handle system commands"""
        command = payload.get("command")
        if command == "restart":
            print("[Main] Restart command received")
            self.shutdown()
            sys.exit(0)
        elif command == "status":
            print("[Main] Status request received")
            self.display.show_status_screen()
        else:
            print(f"[Main] Unknown system command: {command}")
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n[Main] Received signal {signum}, shutting down...")
        self.running = False
        
    def shutdown(self):
        """Graceful shutdown"""
        print("[Main] Shutting down...")
        
        if self.http_server:
            self.http_server.stop_server()
            
        if self.display:
            self.display.shutdown()
            
        print("[Main] ✅ Shutdown complete")

def main():
    """Main entry point"""
    setup_logging()
    
    print("=" * 50)
    print("E-Paper Junction Relay v1.0.0")
    print("Python implementation of Junction Relay protocol")
    print("=" * 50)
    
    relay = EPaperJunctionRelay()
    success = relay.start()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())