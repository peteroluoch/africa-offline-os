# A-OS Hardware Deployment & Hardening Guide

This document is the official reference for deploying A-OS as a robust, "bulletproof" appliance on Raspberry Pi or Debian-based hardware in environments with unstable power.

## 1. Automated Installation
We provide a one-command installer that handles all system dependencies, user permissions, and service registration.

**Command:**
```bash
sudo bash scripts/install.sh
```

**What it does:**
- Installs `python3-venv`, `sqlite3`, `git`, and `curl`.
- Creates a restricted system user `aos-user`.
- Clones/Updates the application in `/app`.
- Sets owner-only permissions (`700`) on the application directory.
- Configures a Python virtual environment and installs requirements.

## 2. Background Service (Systemd)
A-OS is managed as a high-priority system service (`aos.service`) to ensure zero-intervention operation.

- **Start Service:** `sudo systemctl start aos`
- **Check Status:** `sudo systemctl status aos`
- **Auto-Recovery:** If the process crashes or the device is abruptly rebooted, the service will automatically restart within 5 seconds.

## 3. Power Failure Resilience (SQLite)
The database is specifically tuned for "Dirty Shutdowns" (abrupt power cuts):

- **WAL Mode:** Enabled by default in `aos/db/engine.py` for crash-safe operations.
- **Synchronous NORMAL:** Provides a high level of safety against data corruption without the performance penalty of `FULL` sync.
- **Integrity Check:** On every boot, A-OS runs an internal integrity check. If the database is unhealthy, it will log a critical warning to the system journal.

## 4. Security & Lockdown
A-OS follows the principle of least privilege:
- **Restricted User:** The app runs under `aos-user`, which has no access to `/home`, `/root`, or system configuration files.
- **File Lockdown:** The `/app` directory is locked to `700` (Owner-only access).
- **Local Secrets:** All API tokens and passwords stay on the device in the `.env` file.

## 5. Troubleshooting
- **Real-time Logs:** `journalctl -u aos -f`
- **Persistent Log File:** `/app/data/logs/aos.log`
- **Credentials:** If the dashboard is locked, check the `ADMIN_PASSWORD` in your `.env` file.
