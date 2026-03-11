# Raspberry Pi Setup Plan

## Purpose

The Pi is the always-on host for everything that needs to run on a schedule or stay connected 24/7. Your dev machine runs Claude Code and the MCP server — the Pi handles the persistent services.

---

## What Runs on the Pi

| Component | Type | Description |
|---|---|---|
| **Discord bot** | systemd service | Watches `#sb-inbox`, captures thoughts, handles `!brain` and `!prep` commands |
| **Daily digest** | cron — 7am daily | Fetches digest from Supabase Edge Function, sends Discord DM + Gmail |
| **Weekly digest** | cron — Sunday 8am | Same as daily with weekly format |
| **Weekly review** | cron — Sunday 9am | Reflective review including archived thoughts |
| **Nudge check** | cron — 6pm daily | Discord DM prompt if no captures in 2+ days — silent otherwise |
| **Reminder check** | cron — 8am daily | Checks thoughts tagged birthday/anniversary/follow-up/reminder for upcoming dates |

## What Does NOT Run on the Pi

| Component | Where it runs | Why |
|---|---|---|
| **MCP server** | Local machine (dev/work) | Needs to be local to the Claude Code instance |
| **Dashboard** | Browser (any machine) | Static HTML file, no server needed |
| **brain.py / meeting_prep.py** | Dev machine / on demand | CLI tools, run manually when needed |

---

## Hardware

Any Raspberry Pi 3B+ or newer works. Recommended:

- **Raspberry Pi 4 (2GB)** — plenty of headroom, runs cool
- **MicroSD card (16GB+)** — Class 10 / A1 rated
- **Power supply** — official Pi power supply to avoid undervoltage issues
- **Case** — optional but protects the board

The Pi draws ~3–5W idle. Leave it plugged in and forget about it.

---

## Pre-Setup Checklist (do on dev machine first)

- [ ] All Phase 5 scripts built and tested: `digest.py`, `nudge.py`, `remind.py`, `meeting_prep.py`
- [ ] Gmail API authorized (`token.json` exists in project root)
- [ ] `.env` file complete with all required keys (see below)
- [ ] Discord bot token confirmed working

### Required `.env` keys for Pi

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DISCORD_BOT_TOKEN=
DISCORD_USER_ID=
GMAIL_RECIPIENT=
```

> Note: `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are now required — the Discord bot uses them for `!brain` and `!prep` commands.

---

## Setup Steps

### Part A — Flash and configure the SD card

1. Download **Raspberry Pi Imager** from raspberrypi.com/software
2. Flash **Raspberry Pi OS Lite (64-bit)** — no desktop needed
3. Before writing, click the gear icon and configure:
   - Hostname: `secondbrain`
   - Enable SSH
   - Username/password (note these)
   - WiFi SSID + password
4. Insert SD card, power on the Pi
5. Find its IP: check your router's device list or run `ping secondbrain.local`
6. SSH in: `ssh <username>@<pi-ip>`

### Part B — Install git and clone repo

```bash
sudo apt-get update && sudo apt-get install -y git python3-pip
git clone https://github.com/Oniwa/second_brain.git
cd second_brain
```

### Part C — Copy credentials from dev machine

Run these from your **dev machine** (not the Pi):

```bash
# .env file
scp C:/projects/second_brain/.env <username>@<pi-ip>:~/second_brain/.env

# Gmail token (already authorized on dev machine)
scp C:/projects/second_brain/token.json <username>@<pi-ip>:~/second_brain/token.json
```

> `credentials.json` does NOT need to be copied — it's only needed for the one-time `--auth` step, which you already did on your dev machine. Only `token.json` is needed on the Pi.

### Part D — Run the setup script

```bash
sudo python3 scripts/setup_rpi.py
```

This installs:
- Python dependencies (discord.py, aiohttp, google-auth libs)
- Discord bot as a systemd service (auto-starts on boot, auto-restarts on crash)
- Cron jobs for digests, weekly review, and nudge

### Part E — Add the reminder cron job

The setup script needs to be updated to include `remind.py`. Until then, add it manually:

```bash
sudo nano /etc/cron.d/second-brain-digest
```

Add this line:
```
# Reminder check at 8am daily
0 8 * * * <username> /usr/bin/python3 /home/<username>/second_brain/scripts/remind.py >> /home/<username>/second_brain/logs/remind.log 2>&1
```

> **TODO:** Update `scripts/setup_rpi.py` to include the reminder cron job automatically.

### Part F — Verify everything

```bash
# Discord bot running
sudo systemctl status second-brain-bot

# Watch live bot logs
sudo journalctl -u second-brain-bot -f

# Check all cron jobs installed
cat /etc/cron.d/second-brain-digest

# Test digest manually
python3 discord/digest.py --daily

# Test reminder manually
python3 scripts/remind.py --test
```

Post a message in `#sb-inbox` on Discord to confirm the bot is capturing.

---

## Full Cron Schedule

| Time | Job | Log |
|---|---|---|
| 7:00am daily | Daily digest | `logs/digest-daily.log` |
| 8:00am daily | Reminder check | `logs/remind.log` |
| 6:00pm daily | Nudge check | `logs/nudge.log` |
| 8:00am Sunday | Weekly digest | `logs/digest-weekly.log` |
| 9:00am Sunday | Weekly review | `logs/digest-review.log` |

---

## Ongoing Maintenance

### After code changes on dev machine

```bash
# SSH into Pi, pull latest, restart bot
ssh <username>@<pi-ip>
cd second_brain
git pull origin develop
sudo systemctl restart second-brain-bot
```

### Useful commands

```bash
sudo systemctl restart second-brain-bot   # restart after code changes
sudo systemctl stop second-brain-bot      # stop bot
sudo systemctl start second-brain-bot     # start bot
sudo journalctl -u second-brain-bot -n 50 # last 50 log lines
sudo journalctl -u second-brain-bot -f    # live logs
tail -f logs/digest-daily.log             # watch digest logs
tail -f logs/remind.log                   # watch reminder logs
```

### Log rotation

SD cards have limited write cycles. Add log rotation to prevent logs growing unbounded:

```bash
sudo nano /etc/logrotate.d/second-brain
```

```
/home/<username>/second_brain/logs/*.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

---

## Known TODOs Before Setup

- [ ] Update `scripts/setup_rpi.py` to include `remind.py` cron job and `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` in env check
- [ ] Test `discord/bot.py` `!brain` and `!prep` commands end-to-end before deploying
- [ ] Confirm `token.json` on dev machine is valid before copying to Pi

---

## Future: Google Calendar Integration

When the Google Calendar digest integration is built, the Pi will also need:
- `calendar.readonly` OAuth scope added to `credentials.json`
- Re-run `--auth` on dev machine to generate a new `token.json` with calendar access
- Copy updated `token.json` to Pi

No additional cron jobs needed — the calendar data will be pulled inside the existing digest jobs.
