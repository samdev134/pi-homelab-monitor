#!/usr/bin/env python3
"""Sends the last 24 hours of Pi metrics to Claude and pushes a plain-English summary via ntfy."""
import csv
import json
import os
import urllib.request
from datetime import datetime, timedelta

BASE_DIR = os.path.expanduser("~/homelab-monitor")
LOG_FILE = os.path.join(BASE_DIR, "metrics.csv")
KEY_FILE = os.path.join(BASE_DIR, "claude_key.txt")
TOPIC_FILE = os.path.join(BASE_DIR, "ntfy_topic.txt")
MODEL = "claude-haiku-5-5"

METRICS = ["cpu_temp_c", "cpu_load", "memory_used_pct", "disk_used_pct"]


def read_file(path):
    with open(path) as f:
        return f.read().strip()


def load_last_24h():
    """Read only the readings from the last 24 hours."""
    cutoff = datetime.now() - timedelta(hours=24)
    rows = []
    with open(LOG_FILE, newline="") as f:
        for row in csv.DictReader(f):
            time = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            if time >= cutoff:
                rows.append(row)
    return rows


def calculate_stats(rows):
    """Boil hundreds of readings down to a few key numbers per metric."""
    stats = {"readings": len(rows)}
    for metric in METRICS:
        values = [float(r[metric]) for r in rows]
        peak = max(rows, key=lambda r: float(r[metric]))
        stats[metric] = {
            "min": min(values),
            "max": max(values),
            "average": round(sum(values) / len(values), 2),
            "peak_time": peak["timestamp"][11:16],
        }
    # If uptime goes down between readings, the Pi restarted
    stats["restarts"] = sum(
        1 for a, b in zip(rows, rows[1:])
        if float(b["uptime_hours"]) < float(a["uptime_hours"])
    )
    return stats


def ask_claude(stats):
    """Send the stats to Claude and get a short plain-English report back."""
    prompt = (
        "You are monitoring a Raspberry Pi 1 home server. "
        "Write a short daily health report for a phone notification: "
        "max 3 sentences, plain English, no markdown. "
        "Point out anything unusual. Normal ranges: temperature under 60C, "
        "CPU load under 1.5, memory under 85%, disk under 85%. "
        f"Here are the stats for the last 24 hours: {json.dumps(stats)}"
    )
    body = {
        "model": MODEL,
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": read_file(KEY_FILE),
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)

    # The reply can contain several blocks; find the text one
    for block in data["content"]:
        if block.get("type") == "text":
            return block["text"].strip()
    raise ValueError(f"No text in response: {data}")


def send_notification(title, message):
    request = urllib.request.Request(
        f"https://ntfy.sh/{read_file(TOPIC_FILE)}",
        data=message.encode(),
        headers={"Title": title},
    )
    urllib.request.urlopen(request, timeout=10)


def main():
    rows = load_last_24h()
    if not rows:
        print("No readings in the last 24 hours")
        return

    stats = calculate_stats(rows)
    print(json.dumps(stats, indent=2))

    try:
        summary = ask_claude(stats)
    except Exception as e:
        summary = f"Could not get AI summary: {e}"

    print(summary)
    send_notification("sampi daily report", summary)


if __name__ == "__main__":
    main()
