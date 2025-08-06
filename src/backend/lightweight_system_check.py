#!/usr/bin/env python3
import sys
import os
import platform
import subprocess
import shutil
import json

def get_ram_gb():
    """Get RAM in GB using platform-specific methods"""
    try:
        if platform.system() == "Windows":
            # Windows: use wmic command
            result = subprocess.run(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    memory_kb = int(lines[1].strip()) / 1024  # Convert to MBcleacle
                    return memory_kb / 1024  # Convert to GB
                    
        elif platform.system() == "Linux":
            # Linux: read from /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if 'MemTotal' in line:
                        memory_kb = int(line.split()[1])
                        return memory_kb / 1024 / 1024  # Convert to GB
                        
        elif platform.system() == "Darwin":  # macOS
            # macOS: use sysctl command
            result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                memory_bytes = int(result.stdout.strip())
                return memory_bytes / 1024 / 1024 / 1024  # Convert to GB
                
    except Exception as e:
        print(f"Error getting RAM info: {e}", file=sys.stderr)
        
    # Fallback: return a conservative estimate
    return 8.0

def check_gpu():
    """Check GPU availability using nvidia-smi"""
    try:
        # Try to run nvidia-smi to check for NVIDIA GPU
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            # Parse GPU memory
            gpu_memory_mb = float(result.stdout.strip())
            gpu_memory_gb = gpu_memory_mb / 1024
            return True, gpu_memory_gb
        else:
            return False, 0
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        return False, 0

def check_system_requirements():
    """Lightweight system requirements check"""
    try:
        # Get RAM information
        ram_gb = get_ram_gb()
        
        # Get storage information
        storage_gb = shutil.disk_usage('/').free / (1024**3)
        
        # Check GPU availability
        gpu_available, gpu_memory_gb = check_gpu()
        
        # Determine if fine-tuning is possible
        can_fine_tune = (
            ram_gb >= 8 and  # Minimum 8GB RAM
            storage_gb >= 5 and  # Minimum 5GB free space
            (gpu_available or ram_gb >= 16)  # GPU or 16GB+ RAM
        )
        
        return {
            "ram_gb": ram_gb,
            "storage_gb": storage_gb,
            "gpu_available": gpu_available,
            "gpu_memory_gb": gpu_memory_gb,
            "can_fine_tune": can_fine_tune
        }
        
    except Exception as e:
        print(f"Error checking system requirements: {e}", file=sys.stderr)
        return {
            "ram_gb": 8.0,
            "storage_gb": 10.0,
            "gpu_available": False,
            "gpu_memory_gb": 0,
            "can_fine_tune": True  # Assume compatible
        }

if __name__ == "__main__":
    result = check_system_requirements()
    print(json.dumps(result)) 