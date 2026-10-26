# Pi Homelab Monitor

A lightweight monitoring tool running on a repurposed Raspberry Pi 1 Model B (2012).

## Background
This Pi was previously used as an information display kiosk in a workplace. I wiped it, installed Raspberry Pi OS Lite and turned it into a home server that I manage remotely over SSH. This project is the first service running on it.

## What it does
Every 5 minutes, a cron job runs `monitor.py`, which records:
- CPU temperature
- CPU load (1-minute average)
- Memory usage
- SD card storage usage
- Uptime

Each reading is appended to `metrics.csv`. The script reads directly from Linux system files (`/proc/meminfo`, `/proc/uptime`, `/sys/class/thermal`), so it needs no extra packages. That matters on a single-core 700MHz Pi with 512MB of RAM.

## Example output
```
timestamp,cpu_temp_c,cpu_load,memory_used_pct,disk_used_pct,uptime_hours
2026-10-26 17:56:23,37.4,0.08,26.4,15.0,0.99
```

## Setup
```
git clone git@github.com:samdev134/pi-homelab-monitor.git ~/homelab-monitor
cd ~/homelab-monitor
python3 monitor.py
```
To run it every 5 minutes, add this with `crontab -e`:
```
*/5 * * * * /usr/bin/python3 /home/<your-user>/homelab-monitor/monitor.py
```

## Hardware
- Raspberry Pi 1 Model B
- Raspberry Pi OS Lite (32-bit)
- Wired ethernet (no Wi-Fi on this model)

## Roadmap
- [x] Log system metrics on a schedule
- [x] Web dashboard with charts
- [ ] Alerts for high temperature or low disk space
- [ ] AI-generated plain-English health summaries
