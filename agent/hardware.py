"""
Hardware Monitor Module for PC Status
Ultra-lightweight collector for CPU, RAM, Battery, Temperature, Network, and Processes.
"""
import time
import os
import sys
import psutil

try:
    import wmi
    wmi_obj = wmi.WMI()
except Exception:
    wmi_obj = None

_last_net_io = None
_last_net_time = None

def get_cpu_temperature():
    """Attempt to get CPU temperature on Windows via WMI or OHM/LHM."""
    temps = []
    
    try:
        if hasattr(psutil, "sensors_temperatures"):
            st = psutil.sensors_temperatures()
            if st:
                for name, entries in st.items():
                    for entry in entries:
                        if entry.current and entry.current > 0:
                            temps.append(entry.current)
    except Exception:
        pass

    if temps:
        return round(sum(temps) / len(temps), 1)

    if wmi_obj:
        try:
            wmi_ohm = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperature_infos = wmi_ohm.Sensor()
            for sensor in temperature_infos:
                if sensor.SensorType == 'Temperature' and 'CPU' in sensor.Name:
                    if sensor.Value and sensor.Value > 0:
                        temps.append(float(sensor.Value))
        except Exception:
            pass

    if temps:
        return round(max(temps), 1)

    if wmi_obj:
        try:
            wmi_thermal = wmi.WMI(namespace="root\\wmi")
            thermal_zones = wmi_thermal.MSAcpi_ThermalZoneTemperature()
            for zone in thermal_zones:
                celsius = (zone.CurrentTemperature - 2732) / 10.0
                if 0 < celsius < 120:
                    temps.append(celsius)
        except Exception:
            pass

    if temps:
        return round(max(temps), 1)

    return None

def get_network_speed():
    """Calculate current upload and download speed in KB/s."""
    global _last_net_io, _last_net_time
    current_io = psutil.net_io_counters()
    current_time = time.time()
    
    if _last_net_io is None or _last_net_time is None:
        _last_net_io = current_io
        _last_net_time = current_time
        return {"download_kbs": 0.0, "upload_kbs": 0.0}
    
    time_diff = current_time - _last_net_time
    if time_diff <= 0:
        time_diff = 1.0
        
    download_kbs = ((current_io.bytes_recv - _last_net_io.bytes_recv) / 1024.0) / time_diff
    upload_kbs = ((current_io.bytes_sent - _last_net_io.bytes_sent) / 1024.0) / time_diff
    
    _last_net_io = current_io
    _last_net_time = current_time
    
    return {
        "download_kbs": round(download_kbs, 1),
        "upload_kbs": round(upload_kbs, 1)
    }

def get_battery_info():
    """Get battery status and percentage."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            secs = battery.secsleft
            time_left_str = "Desconocido"
            if secs == psutil.POWER_TIME_UNLIMITED:
                time_left_str = "Conectado a la corriente"
            elif secs != psutil.POWER_TIME_UNKNOWN and secs > 0:
                mins = secs // 60
                hrs = mins // 60
                time_left_str = f"{hrs}h {mins % 60}m restantes"
                
            return {
                "present": True,
                "percent": round(battery.percent, 1),
                "plugged": battery.power_plugged,
                "time_left": time_left_str
            }
    except Exception:
        pass
    
    return {
        "present": False,
        "percent": 100,
        "plugged": True,
        "time_left": "Equipo de Escritorio / Sin Batería"
    }

def get_top_processes(limit=10):
    """Retrieve top running processes by CPU & Memory usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
        try:
            info = proc.info
            if info['name'] and info['pid'] != 0:
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "cpu_percent": round(info['cpu_percent'] or 0.0, 1),
                    "memory_percent": round(info['memory_percent'] or 0.0, 1)
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    sorted_procs = sorted(processes, key=lambda p: (p['cpu_percent'], p['memory_percent']), reverse=True)
    return sorted_procs[:limit]

def get_full_telemetry():
    """Collect all hardware metrics into a clean dictionary."""
    cpu_overall = psutil.cpu_percent(interval=None)
    cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
    cpu_freq = psutil.cpu_freq()
    
    mem = psutil.virtual_memory()
    net = get_network_speed()
    battery = get_battery_info()
    cpu_temp = get_cpu_temperature()
    
    disks = []
    for partition in psutil.disk_partitions(all=False):
        if os.name == 'nt' and 'cdrom' in partition.opts:
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "percent": usage.percent
            })
        except Exception:
            pass

    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    return {
        "timestamp": int(time.time()),
        "hostname": os.environ.get('COMPUTERNAME', 'PC-Host'),
        "os": sys.platform,
        "uptime": uptime_str,
        "cpu": {
            "percent": cpu_overall,
            "cores": cpu_per_core,
            "count": psutil.cpu_count(logical=True),
            "freq_mhz": round(cpu_freq.current, 0) if cpu_freq else None,
            "temp_c": cpu_temp
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round((mem.total - mem.available) / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent
        },
        "battery": battery,
        "network": net,
        "disks": disks,
        "top_processes": get_top_processes(limit=10)
    }

if __name__ == "__main__":
    import json
    print("Capturando telemetría de prueba...")
    data = get_full_telemetry()
    print(json.dumps(data, indent=2, ensure_ascii=False))
