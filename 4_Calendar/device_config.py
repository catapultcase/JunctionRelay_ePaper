"""
Device Configuration - Manages device settings and preferences
"""

import json
import os
from typing import Dict, Any, Optional

class DeviceConfig:
    """Manages device configuration and preferences"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = {}
        self._load_config()
        
    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                print(f"[DeviceConfig] Loaded config from {self.config_file}")
            except Exception as e:
                print(f"[DeviceConfig] ERROR loading config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
            
    def _create_default_config(self):
        """Create default configuration"""
        self.config = {
            "device": {
                "name": "EPaperJunctionRelay",
                "version": "1.0.0",
                "mac_address": self._get_mac_address()
            },
            "display": {
                "refresh_interval": 60,
                "show_debug": False,
                "theme": "default"
            },
            "network": {
                "http_port": 80,
                "enable_cors": True
            },
            "data": {
                "sensor_retention_hours": 24,
                "auto_clear_old_data": True
            }
        }
        self._save_config()
        print("[DeviceConfig] Created default configuration")
        
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[DeviceConfig] ERROR saving config: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        self._save_config()
        
    def _get_mac_address(self) -> str:
        """Get system MAC address"""
        try:
            import uuid
            return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                           for ele in range(0,8*6,8)][::-1])
        except:
            return "00:00:00:00:00:00"