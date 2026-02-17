#!/usr/bin/env python3
"""
on-exit_tod.py - Time of Day context filter for Taskwarrior 2.6.2
Version: 0.1.1

Updates context.tod.read in tod.rc with negative tags for non-matching
time blocks, so tasks tagged for other times of day are hidden when
the 'tod' context is active.

Install:
  cp on-exit_tod.py ~/.task/hooks/on-exit_tod.py
  chmod +x ~/.task/hooks/on-exit_tod.py
  echo 'include ~/.task/config/tod.rc' >> ~/.taskrc
"""

import sys
import os
import json
import subprocess
from datetime import datetime

VERSION = "0.1.1"
TOD_RC = os.path.expanduser("~/.task/config/tod.rc")
GENERATED_MARKER = "context.tod.read="
DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# Debug logging - set DEBUG_TOD=1 to enable
DEBUG = os.environ.get("DEBUG_TOD", "0") == "1"
LOG_FILE = os.path.expanduser("~/.task/hooks/tod_debug.log")


def debug_log(msg):
    if not DEBUG:
        return
    try:
        with open(LOG_FILE, "a") as f:
            f.write("{} [tod-exit] {}\n".format(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass

def get_tod_blocks():
    blocks = {}
    try:
        with open(TOD_RC, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("tod.block."):
                    key, _, val = line.partition("=")
                    name = key.replace("tod.block.", "")
                    if val:
                        blocks[name] = val.strip()
    except Exception as e:
        debug_log("Error reading tod.rc: {}".format(e))
    return blocks

def parse_time(t):
    """Parse HH:MM string to (hour, minute) tuple."""
    parts = t.strip().split(":")
    return int(parts[0]), int(parts[1])


def is_time_block(value):
    """Check if a block value is a time range (contains ':')."""
    return ":" in value


def is_day_block(value):
    """Check if a block value is a day-of-week list."""
    parts = [p.strip().lower() for p in value.split(",")]
    return all(p in DAY_NAMES for p in parts)


def time_in_range(now_h, now_m, start_h, start_m, end_h, end_m):
    """Check if current time falls within range, handling overnight wrap."""
    now_minutes = now_h * 60 + now_m
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if start_minutes <= end_minutes:
        # Normal range: 08:00-18:00
        return start_minutes <= now_minutes < end_minutes
    else:
        # Overnight range: 22:00-07:00
        return now_minutes >= start_minutes or now_minutes < end_minutes


def block_matches_now(value, now=None):
    """Determine if a block definition matches the current time/day."""
    if now is None:
        now = datetime.now()

    if is_time_block(value):
        parts = value.split("-")
        if len(parts) != 2:
            debug_log("Bad time range: {}".format(value))
            return False
        start_h, start_m = parse_time(parts[0])
        end_h, end_m = parse_time(parts[1])
        return time_in_range(now.hour, now.minute, start_h, start_m, end_h, end_m)

    elif is_day_block(value):
        today = DAY_NAMES[now.weekday()]
        days = [d.strip().lower() for d in value.split(",")]
        return today in days

    else:
        debug_log("Unrecognized block format: {}".format(value))
        return False


def build_filter(blocks, now=None):
    """Build the negative tag filter string from non-matching blocks."""
    matching = []
    non_matching = []

    for name, value in sorted(blocks.items()):
        if block_matches_now(value, now):
            matching.append(name)
        else:
            non_matching.append(name)

    debug_log("Matching blocks: {}".format(matching))
    debug_log("Non-matching blocks: {}".format(non_matching))

    if not non_matching:
        return ""

    # Build filter: -morn -aft -nite etc
    tags = " ".join("-{}".format(name) for name in sorted(non_matching))
    return tags


def update_rc(new_filter):
    """Update context.tod.read in tod.rc, only if changed."""
    if not os.path.exists(TOD_RC):
        debug_log("tod.rc not found at {}".format(TOD_RC))
        return False

    try:
        with open(TOD_RC, "r") as f:
            lines = f.readlines()
    except Exception as e:
        debug_log("Error reading tod.rc: {}".format(e))
        return False

    new_line = "{}{}\n".format(GENERATED_MARKER, new_filter)
    changed = False
    found = False

    for i, line in enumerate(lines):
        if line.startswith(GENERATED_MARKER):
            found = True
            if line != new_line:
                lines[i] = new_line
                changed = True
            break

    if not found:
        lines.append(new_line)
        changed = True

    if changed:
        try:
            with open(TOD_RC, "w") as f:
                f.writelines(lines)
            debug_log("Updated tod.rc: {}".format(new_filter))
        except Exception as e:
            debug_log("Error writing tod.rc: {}".format(e))
            return False

    return changed


def main():
    # on-exit hook: consume stdin but do NOT echo it back
    # (on-exit protocol: outputting JSON would cause "Expected 0, found N" errors)
    sys.stdin.readlines()

    # Do our work
    blocks = get_tod_blocks()
    if not blocks:
        debug_log("No tod.block.* entries found in config")
        sys.exit(0)

    now = datetime.now()
    debug_log("Current time: {}".format(now.strftime("%A %H:%M")))

    new_filter = build_filter(blocks, now)
    changed = update_rc(new_filter)

    if changed:
        debug_log("Context filter updated")

    sys.exit(0)


if __name__ == "__main__":
    main()
