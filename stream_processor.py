"""
Stream Processor - Handles the 4 Junction Relay data types
Replicates the C++ StreamProcessor functionality
"""

import gzip
import json
import threading
from typing import Callable, Optional, Dict, Any
from queue import Queue, Empty
from utils import log_debug

class StreamProcessor:
    """
    Processes Junction Relay protocol data:
    - Type 1: Raw JSON (starts with '{')
    - Type 2: Prefixed JSON (8-byte prefix + JSON)
    - Type 3: Raw Gzip (starts with 0x1F 0x8B)
    - Type 4: Prefixed Gzip (8-byte prefix + compressed JSON)
    """
    
    MAX_PAYLOAD_SIZE = 8192
    SENSOR_QUEUE_SIZE = 30
    CONFIG_QUEUE_SIZE = 3
    
    def __init__(self, display_callback: Callable, system_callback: Callable):
        self.display_callback = display_callback
        self.system_callback = system_callback
        
        # Stream state
        self.reading_length = True
        self.bytes_read = 0
        self.payload_length = 0
        self.prefix_buffer = bytearray(8)
        self.payload_buffer = bytearray(self.MAX_PAYLOAD_SIZE)
        
        # Parsed prefix fields
        self.length_hint = 0
        self.type_field = 0
        self.route_field = 0
        
        # Statistics
        self.messages_processed = 0
        self.error_count = 0
        
        # Background processing queues
        self.sensor_queue = Queue(maxsize=self.SENSOR_QUEUE_SIZE)
        self.config_queue = Queue(maxsize=self.CONFIG_QUEUE_SIZE)
        
        # Start background processing threads
        self.running = True
        self.sensor_thread = threading.Thread(target=self._process_sensor_queue, daemon=True)
        self.config_thread = threading.Thread(target=self._process_config_queue, daemon=True)
        self.sensor_thread.start()
        self.config_thread.start()
        
        print("[StreamProcessor] Initialized with background processing")
        
    def process_data(self, data: bytes) -> None:
        """Main data processing entry point"""
        if not data:
            return
            
        # Enhanced payload detection for 4 types
        if self.reading_length and self.bytes_read == 0 and len(data) > 0:
            # Type 1: Raw JSON
            if data[0] == ord('{'):
                self._handle_raw_json(data)
                return
                
            # Type 3: Raw Gzip
            if len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B:
                self._handle_raw_gzip(data)
                return
                
        # Handle prefixed data (Types 2 & 4)
        self._process_prefixed_data(data)
        
    def _process_prefixed_data(self, data: bytes):
        """Process data with 8-byte prefix"""
        data_len = len(data)
        offset = 0
        
        # Stage 1: Read 8-byte prefix
        if self.reading_length:
            prefix_needed = 8 - self.bytes_read
            prefix_copy_len = min(data_len, prefix_needed)
            
            self.prefix_buffer[self.bytes_read:self.bytes_read + prefix_copy_len] = data[offset:offset + prefix_copy_len]
            self.bytes_read += prefix_copy_len
            offset += prefix_copy_len
            
            if self.bytes_read >= 8:
                if not self._parse_prefix():
                    self._reset_stream_state()
                    return
                    
                self.reading_length = False
                self.bytes_read = 0
                
        # Stage 2: Read payload data
        if not self.reading_length and offset < data_len:
            remaining_bytes = self.payload_length - self.bytes_read
            copy_len = min(data_len - offset, remaining_bytes)
            
            if self.bytes_read + copy_len <= self.MAX_PAYLOAD_SIZE:
                self.payload_buffer[self.bytes_read:self.bytes_read + copy_len] = data[offset:offset + copy_len]
                self.bytes_read += copy_len
            else:
                print(f"[StreamProcessor] ERROR: Payload buffer overflow")
                self._reset_stream_state()
                return
                
        # Stage 3: Process complete payload
        if not self.reading_length and self.bytes_read >= self.payload_length:
            self._handle_prefixed_payload()
            
    def _parse_prefix(self) -> bool:
        """Parse 8-byte prefix: LLLLTTRR"""
        try:
            prefix_str = self.prefix_buffer.decode('ascii')
            
            # Validate all digits
            if not prefix_str.isdigit():
                print(f"[StreamProcessor] ERROR: Invalid prefix format: {prefix_str}")
                return False
                
            self.length_hint = int(prefix_str[0:4])
            self.type_field = int(prefix_str[4:6])
            self.route_field = int(prefix_str[6:8])
            
            # Validate type field
            if self.type_field not in [0, 1]:
                print(f"[StreamProcessor] ERROR: Invalid type field: {self.type_field:02d}")
                return False
                
            # Set payload length
            if self.length_hint > 0:
                self.payload_length = self.length_hint
            else:
                self.payload_length = self.MAX_PAYLOAD_SIZE
                print("[StreamProcessor] WARNING: Length hint is 0000, using auto-detection")
                
            return True
            
        except Exception as e:
            print(f"[StreamProcessor] ERROR: Prefix parsing failed: {e}")
            return False
            
    def _handle_raw_json(self, data: bytes):
        """Handle Type 1: Raw JSON"""
        log_debug("[StreamProcessor] Processing Raw JSON (Type 1)")
        self._forward_to_router(data)
        self.messages_processed += 1
        
    def _handle_raw_gzip(self, data: bytes):
        """Handle Type 3: Raw Gzip"""
        log_debug("[StreamProcessor] Processing Raw Gzip (Type 3)")
        try:
            decompressed = gzip.decompress(data)
            self._forward_to_router(decompressed)
            self.messages_processed += 1
        except Exception as e:
            print(f"[StreamProcessor] ERROR: Gzip decompression failed: {e}")
            self.error_count += 1
            
    def _handle_prefixed_payload(self):
        """Handle Types 2 & 4: Prefixed payloads"""
        payload_data = bytes(self.payload_buffer[:self.payload_length])
        
        if self.type_field == 0:
            # Type 2: Prefixed JSON
            log_debug(f"[StreamProcessor] Processing Prefixed JSON (Type 2), Route: {self.route_field:02d}")
            self._forward_to_router(payload_data)
        elif self.type_field == 1:
            # Type 4: Prefixed Gzip
            log_debug(f"[StreamProcessor] Processing Prefixed Gzip (Type 4), Route: {self.route_field:02d}")
            try:
                decompressed = gzip.decompress(payload_data)
                self._forward_to_router(decompressed)
            except Exception as e:
                print(f"[StreamProcessor] ERROR: Prefixed gzip decompression failed: {e}")
                self.error_count += 1
                self._reset_stream_state()
                return
                
        self.messages_processed += 1
        self._reset_stream_state()
        
    def _forward_to_router(self, data: bytes):
        """Parse JSON and route to appropriate handler"""
        try:
            json_str = data.decode('utf-8')
            payload = json.loads(json_str)
            
            # Check for destination routing
            if "destination" in payload:
                # Handle destination routing if needed
                print(f"[StreamProcessor] Message with destination: {payload['destination']}")
                # For now, process locally - could add forwarding logic
                
            data_type = payload.get("type", "unknown")
            
            if data_type == "sensor":
                # Queue for background processing
                try:
                    self.sensor_queue.put_nowait(payload)
                except:
                    print("[StreamProcessor] Sensor queue full, processing immediately")
                    self.display_callback("sensor", payload)
                    
            elif data_type == "config":
                # Queue for background processing  
                try:
                    self.config_queue.put_nowait(payload)
                except:
                    print("[StreamProcessor] Config queue full, processing immediately")
                    self.display_callback("config", payload)
                    
            elif data_type in ["device_info", "preferences", "system_command", "stats"]:
                # System callbacks - process immediately
                self.system_callback(data_type, payload)
                
            else:
                print(f"[StreamProcessor] Unknown message type: {data_type}")
                self.system_callback("unknown", payload)
                
        except json.JSONDecodeError as e:
            print(f"[StreamProcessor] ERROR: JSON parsing failed: {e}")
            self.error_count += 1
        except Exception as e:
            print(f"[StreamProcessor] ERROR: Routing failed: {e}")
            self.error_count += 1
            
    def _process_sensor_queue(self):
        """Background thread for sensor data processing"""
        while self.running:
            try:
                payload = self.sensor_queue.get(timeout=1.0)
                # Ensure payload is a dictionary
                if isinstance(payload, str):
                    import json
                    payload = json.loads(payload)
                self.display_callback("sensor", payload)
                self.sensor_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"[StreamProcessor] ERROR in sensor processing: {e}")
                print(f"[StreamProcessor] Payload type: {type(payload)}, Content: {payload}")
                
    def _process_config_queue(self):
        """Background thread for config data processing"""
        while self.running:
            try:
                payload = self.config_queue.get(timeout=1.0)
                # Ensure payload is a dictionary
                if isinstance(payload, str):
                    import json
                    payload = json.loads(payload)
                self.display_callback("config", payload)
                self.config_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"[StreamProcessor] ERROR in config processing: {e}")
                print(f"[StreamProcessor] Payload type: {type(payload)}, Content: {payload}")
                
    def _reset_stream_state(self):
        """Reset stream parsing state"""
        self.reading_length = True
        self.bytes_read = 0
        self.payload_length = 0
        self.length_hint = 0
        self.type_field = 0
        self.route_field = 0
        self.prefix_buffer = bytearray(8)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "messages_processed": self.messages_processed,
            "error_count": self.error_count,
            "sensor_queue_size": self.sensor_queue.qsize(),
            "config_queue_size": self.config_queue.qsize(),
            "max_payload_size": self.MAX_PAYLOAD_SIZE
        }
        
    def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        print("[StreamProcessor] Shutdown complete")