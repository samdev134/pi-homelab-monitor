#!/usr/bin/env python3
"""Logs Raspberry Pi health metrics to a CSV file and sends alerts."""
import csv
import json
import os
import shutil
import urllib.request
from datetime import datetime

BASE_DIR = os.path.expanduser("~/homelab-monitor")
LOG_FILE = os.path.join(BASE_DIR, "metrics.csv")
STATE_FILE = os.path.join(BASE_DIR, "alert_state.json")
TOPIC_FILE = os.path.join(BASE_DIR, "ntfy_topic.txt")

# Alert when a metric goes above these limits
THRESHOLDS = {
    "cpu_temp_c": 60,
    "cpu_load": 1.5,
    "memory_used_pct": 85,
    "disk_used_pct": 85,
}


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


def send_alert(message):
    """Send a push notification via ntfy."""
    try:
        with open(TOPIC_FILE) as f:
            topic = f.read().strip()
    except FileNotFoundError:
        print("No ntfy topic set, skipping alert")
        return

    request = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode(),
        headers={"Title": "sampi alert"},
    )
    try:
        urllib.request.urlopen(request, timeout=10)
        print(f"Alert sent: {message}")
    except Exception as e:
        print(f"Could not send alert: {e}")


def check_alerts(row):
    """Alert once when a metric goes over its limit, and once when it recovers."""
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}

    for metric, limit in THRESHOLDS.items():
        too_high = row[metric] > limit
        was_alerting = state.get(metric, False)

        if too_high and not was_alerting:
            send_alert(f"{metric} is {row[metric]} (limit {limit})")
        elif not too_high and was_alerting:
            send_alert(f"{metric} back to normal: {row[metric]}")

        state[metric] = too_high

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


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
    check_alerts(row)


if __name__ == "__main__":
    main()
