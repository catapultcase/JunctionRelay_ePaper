"""
Utilities - Shared helper functions
"""

import logging
import time
import uuid
from typing import Dict, Any

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

def log_debug(message: str):
    """Debug logging (can be disabled for production)"""
    # Uncomment for debug output:
    # print(message)
    pass

def get_mac_address() -> str:
    """Get formatted MAC address"""
    try:
        mac = uuid.getnode()
        return ':'.join(['{:02x}'.format((mac >> ele) & 0xff) 
                        for ele in range(0,8*6,8)][::-1])
    except:
        return "00:00:00:00:00:00"

def get_system_stats() -> Dict[str, Any]:
    """Get system statistics"""
    try:
        import psutil
        
        # CPU and memory stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Uptime
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        return {
            "cpu_percent": cpu_percent,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": disk.percent,
            "uptime": int(uptime),
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
    except Exception as e:
        print(f"[Utils] ERROR getting system stats: {e}")
        return {
            "cpu_percent": 0,
            "memory_total": 0,
            "memory_used": 0,
            "memory_percent": 0,
            "uptime": 0
        }