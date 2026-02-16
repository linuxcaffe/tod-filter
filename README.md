- Project: https://github.com/linuxcaffe/tw-tod-hook
- Issues:  https://github.com/linuxcaffe/tw-tod-hook/issues

# tw-tod-hook

A Taskwarrior on-launch hook that automatically filters tasks by time of day.

---

## TL;DR

- Tag tasks with `+morn`, `+aft`, `+eve`, `+nite`, `+day`, `+wkday`, `+wkend`
- Hook maintains a `tod` context with negative filters for non-matching times
- Activate with `task context tod` — untagged tasks always remain visible
- Configurable time blocks, overnight ranges, and day-of-week support

---

## Why this exists

A long task list is noisy. Many tasks are only actionable at certain times —
phone calls in the morning, errands in the afternoon, hobbies in the evening.
Filtering *for* a time of day hides everything without that tag, which is
dangerous. Important untagged tasks disappear.

This hook takes the opposite approach: it filters *out* tasks tagged for other
times of day. Untagged tasks stay visible. Nothing important gets hidden.

---

## Core concepts

- **Time blocks**
  Named time ranges defined in `tod.rc`. Each block name corresponds to a tag.
  `tod.block.morn=08:00-12:00` means the `+morn` tag is active from 8am to noon.

- **Day blocks**
  Day-of-week filters. `tod.block.wkend=sat,sun` means `+wkend` tasks are
  relevant on weekends.

- **Negative filtering**
  The hook determines which blocks do *not* match the current time, and builds
  a context filter that hides those tags. If it's evening, tasks tagged `+morn`, `+day`
  and `+aft` are hidden — everything else shows through.

- **Context-based**
  The filter is stored as `context.tod.read`, a standard Taskwarrior context.
  It stacks with other context systems and applies to all reports.

---

## Example workflow

1. Tag some tasks:

```
task add "call dentist" +morn
task add "grocery run" +aft
task add "watch documentary" +eve
task add "backup servers" +nite
task add "mow lawn" +wkend
task add "fix that bug"
```

2. Activate the context:

```
task context tod
```

3. At 9am on a Tuesday, `task list` shows:
   - ✓ "call dentist" (+morn — matches)
   - ✗ "grocery run" (+aft — hidden)
   - ✗ "watch documentary" (+eve — hidden)
   - ✗ "backup servers" (+nite — hidden)
   - ✗ "mow lawn" (+wkend — hidden, it's a weekday)
   - ✓ "fix that bug" (no ToD tag — always visible)

4. At 7pm, the filter updates automatically — now `+eve` tasks appear,
   `+morn` and `+aft` are hidden.

---

## Installation

### Option #1 - clone this repo and use the included install script

```
./tod-filter.install
```

Installs hook, tod.rc and README.md in correct folders under ~/.task

### Option #2 - via awesome-taskwarrior's package manager

```
tw -I tod-filter
```

### Option #3 - manual 

```
cp on-launch-tod.py ~/.task/hooks/
chmod +x ~/.task/hooks/on-launch-tod.py
cp tod.rc ~/.task/config/
echo 'include ~/.task/config/tod.rc' >> ~/.taskrc
```

---

## Configuration

Edit `~/.task/config/tod.rc` to customize time blocks:

```
tod.block.morn=08:00-12:00
tod.block.aft=12:00-18:00
tod.block.eve=18:00-22:00
tod.block.nite=22:00-07:00
tod.block.day=08:00-18:00
tod.block.wkday=mon,tue,wed,thu,fri
tod.block.wkend=sat,sun
```

Overnight ranges (where start > end) are handled correctly — `22:00-07:00`
means 10pm through 7am the next morning.

---

## Usage

```
task context tod          # activate time-of-day filtering
task context none         # turn it off
```

The hook updates the context filter on every `task` invocation. No cron jobs,
no manual switching — it just follows the clock.

---

## Debugging

```
DEBUG_TOD=1 task list
cat ~/.task/hooks/tod_debug.log
```

---

## Project status

⚠️ Early / experimental

- Core functionality working
- Configuration format may change
- Feedback welcome

---

## Metadata

- License: MIT
- Language: Python
- Requires: Taskwarrior 2.6.2
- Platforms: Linux
