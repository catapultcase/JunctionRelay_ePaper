"""
E-Paper Hardware Wrapper - REAL HARDWARE ONLY (with timeout handling)
Forces real hardware initialization and fails if hardware isn't available
"""

import os
import sys
import subprocess
import glob
import signal
import threading

# Add lib directory to path
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.insert(0, libdir)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

class EPaperDisplay:
    """Wrapper class that ONLY works with real e-paper hardware"""
    
    def __init__(self):
        self.epd = None
        self.width = 792
        self.height = 272
        self.is_hardware = False
        self._force_real_hardware()
        
    def _force_real_hardware(self):
        """Force real hardware initialization - no mocking allowed"""
        
        # First, verify we have access to GPIO hardware
        if not self._verify_gpio_access():
            raise RuntimeError("GPIO hardware not accessible - real e-paper display required")
            
        # Verify SPI access
        if not self._verify_spi_access():
            raise RuntimeError("SPI hardware not accessible - real e-paper display required")
            
        try:
            # Import the real waveshare library without any mocking
            print("[EPaperDisplay] Attempting to load real Waveshare hardware driver...")
            
            from waveshare_epd import epd5in79g
            
            # Create the real EPD instance
            self.epd = epd5in79g.EPD()
            self.width = getattr(self.epd, 'width', 792)
            self.height = getattr(self.epd, 'height', 272)
            self.is_hardware = True
            
            print("[EPaperDisplay] Real hardware driver loaded successfully")
            
        except Exception as e:
            print(f"[EPaperDisplay] FAILED to load real hardware driver: {e}")
            raise RuntimeError(f"Real e-paper hardware initialization failed: {e}")
            
    def _verify_gpio_access(self):
        """Verify that GPIO hardware is actually accessible (Pi 5 compatible)"""
        
        # Check for various GPIO device patterns
        gpio_patterns = [
            '/dev/gpiomem',      # Pi 4 and older
            '/dev/gpiomem*',     # Pi 5 style (gpiomem0, gpiomem1, etc.)
            '/dev/gpiochip*',    # GPIO chip devices
            '/sys/class/gpio'    # GPIO sysfs interface
        ]
        
        found_devices = []
        
        for pattern in gpio_patterns:
            if '*' in pattern:
                # Use glob for wildcard patterns
                matches = glob.glob(pattern)
                found_devices.extend(matches)
            else:
                # Check single path
                if os.path.exists(pattern):
                    found_devices.append(pattern)
        
        print(f"[EPaperDisplay] Found GPIO devices: {found_devices}")
        
        if not found_devices:
            print("[EPaperDisplay] No GPIO devices found")
            return False
            
        # Try to find a gpiomem device we can access
        gpiomem_devices = [d for d in found_devices if 'gpiomem' in d]
        
        for device in gpiomem_devices:
            try:
                if os.access(device, os.R_OK | os.W_OK):
                    print(f"[EPaperDisplay] GPIO hardware access verified via {device}")
                    return True
                else:
                    print(f"[EPaperDisplay] No access to {device}")
            except Exception as e:
                print(f"[EPaperDisplay] Error checking {device}: {e}")
                
        # If no gpiomem access, check if we have any GPIO access at all
        gpiochip_devices = [d for d in found_devices if 'gpiochip' in d]
        if gpiochip_devices:
            print(f"[EPaperDisplay] Found GPIO chip devices but may need different access method")
            # On Pi 5, we might need to use gpiochip devices differently
            return True
            
        print("[EPaperDisplay] GPIO hardware access verification failed")
        return False
            
    def _verify_spi_access(self):
        """Verify that SPI hardware is actually accessible"""
        spi_devices = glob.glob('/dev/spidev*')
        
        print(f"[EPaperDisplay] Found SPI devices: {spi_devices}")
        
        if not spi_devices:
            print("[EPaperDisplay] No SPI devices found")
            return False
            
        # Check if we can access at least one SPI device
        for device in spi_devices:
            try:
                if os.access(device, os.R_OK | os.W_OK):
                    print(f"[EPaperDisplay] SPI hardware access verified via {device}")
                    return True
                else:
                    print(f"[EPaperDisplay] No access to {device}")
            except Exception as e:
                print(f"[EPaperDisplay] Error checking {device}: {e}")
        
        print("[EPaperDisplay] SPI hardware access verification failed")
        return False
    
    def _init_with_timeout(self, timeout_seconds=30):
        """Initialize with timeout protection"""
        print(f"[EPaperDisplay] Initializing with {timeout_seconds}s timeout...")
        
        # Set up timeout signal
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            self.epd.init()
            signal.alarm(0)  # Cancel the alarm
            print("[EPaperDisplay] Hardware initialization completed successfully")
            return True
        except TimeoutError:
            print(f"[EPaperDisplay] Hardware initialization timed out after {timeout_seconds}s")
            return False
        except Exception as e:
            signal.alarm(0)  # Cancel the alarm
            print(f"[EPaperDisplay] Hardware initialization failed: {e}")
            return False
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            
    def initialize(self):
        """Initialize the REAL display hardware"""
        if not self.is_hardware:
            raise RuntimeError("No real hardware available - mock displays not allowed")
            
        print("[EPaperDisplay] Initializing real e-paper hardware...")
        
        # Try initialization with timeout
        if self._init_with_timeout(30):
            print("[EPaperDisplay] Real e-paper hardware initialized successfully")
            return True
        else:
            print("[EPaperDisplay] Hardware initialization failed or timed out")
            # Try once more with shorter timeout
            print("[EPaperDisplay] Attempting quick retry...")
            if self._init_with_timeout(10):
                print("[EPaperDisplay] Real e-paper hardware initialized on retry")
                return True
            else:
                raise RuntimeError("Failed to initialize real e-paper hardware after multiple attempts")
            
    def clear(self):
        """Clear the REAL display"""
        if not self.is_hardware:
            raise RuntimeError("No real hardware available")
            
        try:
            print("[EPaperDisplay] Clearing display...")
            self.epd.Clear()
            print("[EPaperDisplay] Real display cleared")
        except Exception as e:
            print(f"[EPaperDisplay] Clear failed: {e}")
            raise
            
    def display(self, image):
        """Update the REAL display with an image"""
        if not self.is_hardware:
            raise RuntimeError("No real hardware available")
            
        try:
            print("[EPaperDisplay] Updating display...")
            buffer = self.epd.getbuffer(image)
            self.epd.display(buffer)
            print("[EPaperDisplay] Real display updated")
        except Exception as e:
            print(f"[EPaperDisplay] Display update failed: {e}")
            raise
            
    def sleep(self):
        """Put REAL display to sleep"""
        if not self.is_hardware:
            raise RuntimeError("No real hardware available")
            
        try:
            print("[EPaperDisplay] Putting display to sleep...")
            self.epd.sleep()
            print("[EPaperDisplay] Real display put to sleep")
        except Exception as e:
            print(f"[EPaperDisplay] Sleep failed: {e}")
            raise
            
    def get_dimensions(self):
        """Get display dimensions"""
        return self.width, self.height