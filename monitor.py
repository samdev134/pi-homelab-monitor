#!/usr/bin/env python3
"""Logs Raspberry Pi health metrics to a CSV file."""
import csv
import os
import shutil
from datetime import datetime

LOG_FILE = os.path.expanduser("~/homelab-monitor/metrics.csv")


def cpu_temp():
    """CPU temperature in degrees C."""
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return round(int(f.read()) / 1000, 1)


def cpu_load():
    """Average CPU load over the last minute."""
    return round(os.getloadavg()[0], 2)


def memory_used_percent():
    """Percentage of RAM in use."""
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":")
            info[key] = int(value.split()[0])
    used = info["MemTotal"] - info["MemAvailable"]
    return round(used / info["MemTotal"] * 100, 1)


def disk_used_percent():
    """Percentage of SD card storage in use."""
    total, used, _ = shutil.disk_usage("/")
    return round(used / total * 100, 1)


def uptime_hours():
    """Hours since last boot."""
    with open("/proc/uptime") as f:
        return round(float(f.read().split()[0]) / 3600, 2)


def main():
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_temp_c": cpu_temp(),
        "cpu_load": cpu_load(),
        "memory_used_pct": memory_used_percent(),
        "disk_used_pct": disk_used_percent(),
        "uptime_hours": uptime_hours(),
    }

    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if new_file:
            writer.writeheader()
        writer.writerow(row)

    print(row)


if __name__ == "__main__":
    main()
