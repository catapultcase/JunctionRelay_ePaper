"""
HTTP Endpoints - Provides REST API for data ingestion
Replicates the Junction Relay HTTP interface
"""

from flask import Flask, request, jsonify
import threading
import time
from typing import Optional
from stream_processor import StreamProcessor
from device_config import DeviceConfig
from utils import get_mac_address, get_system_stats

class HTTPEndpoints:
    """HTTP server providing Junction Relay compatible endpoints"""
    
    def __init__(self, stream_processor: StreamProcessor, config: DeviceConfig):
        self.stream_processor = stream_processor
        self.config = config
        self.app = Flask(__name__)
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup all HTTP endpoints"""
        
        @self.app.route('/api/data', methods=['POST'])
        def handle_data():
            """Main data ingestion endpoint - accepts all 4 Junction Relay data types"""
            try:
                # Get raw binary data
                data = request.get_data()
                
                if not data:
                    return jsonify({"error": "No data received"}), 400
                    
                # Process through StreamProcessor
                self.stream_processor.process_data(data)
                
                return jsonify({"status": "OK"}), 200
                
            except Exception as e:
                print(f"[HTTPEndpoints] ERROR in /api/data: {e}")
                return jsonify({"error": str(e)}), 500
                
        @self.app.route('/api/device/info', methods=['GET'])
        def get_device_info():
            """Device information endpoint"""
            return jsonify({
                "mac_address": get_mac_address(),
                "device_type": "EPaperJunctionRelay",
                "firmware_version": "1.0.0",
                "capabilities": [
                    "epaper_display",
                    "http_ingestion", 
                    "junction_relay_protocol",
                    "onboard_screen"
                ],
                "screens": {
                    "onboard_screen": {
                        "type": "epaper",
                        "width": 792,
                        "height": 272,
                        "colors": ["black", "white", "red", "yellow"],
                        "active": True
                    }
                },
                "display": {
                    "width": 792,
                    "height": 272,
                    "colors": ["black", "white", "red", "yellow"]
                }
            })
            
        @self.app.route('/api/system/stats', methods=['GET'])
        def get_system_stats_endpoint():
            """System statistics endpoint"""
            stream_stats = self.stream_processor.get_stats()
            system_stats = get_system_stats()
            
            return jsonify({
                "system": system_stats,
                "stream_processor": stream_stats,
                "uptime_seconds": system_stats.get("uptime", 0)
            })
            
        @self.app.route('/api/connection/status', methods=['GET'])
        def get_connection_status():
            """Connection status endpoint"""
            return jsonify({
                "status": "connected",
                "protocol": "HTTP",
                "mac_address": get_mac_address(),
                "endpoints_active": True
            })
            
        @self.app.route('/api/health/heartbeat', methods=['GET'])
        def heartbeat():
            """Health check endpoint"""
            return jsonify({
                "status": "OK",
                "timestamp": int(time.time()),
                "service": "epaper_junction_relay"
            })
            
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "Endpoint not found"}), 404
            
        @self.app.errorhandler(500)  
        def internal_error(error):
            return jsonify({"error": "Internal server error"}), 500
            
    def start_server(self, host: str = "0.0.0.0", port: int = 80):
        """Start the HTTP server"""
        if self.running:
            return
            
        self.running = True
        print(f"[HTTPEndpoints] Starting server on {host}:{port}")
        
        try:
            self.app.run(host=host, port=port, debug=False, threaded=True)
        except Exception as e:
            print(f"[HTTPEndpoints] Server error: {e}")
        finally:
            self.running = False
            
    def stop_server(self):
        """Stop the HTTP server"""
        self.running = False
        print("[HTTPEndpoints] Server stopped")