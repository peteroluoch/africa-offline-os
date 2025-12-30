"""
Automated SQLite backup script for production deployment.

Usage:
    python -m aos.scripts.backup_db

Schedule with cron:
    0 */6 * * * cd /app && python -m aos.scripts.backup_db
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def backup_database():
    """
    Create timestamped backup using SQLite's backup API.
    
    This is safer than file copy because it:
    - Handles WAL mode correctly
    - Ensures consistent snapshot
    - Works while database is in use
    """
    db_path = Path(os.getenv("AOS_SQLITE_PATH", "aos.db"))
    backup_dir = Path("/data/backups")
    backup_dir.mkdir(exist_ok=True, parents=True)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"aos_backup_{timestamp}.db"
    
    print(f"[BACKUP] Starting backup: {db_path} -> {backup_path}")
    
    try:
        # Use SQLite's backup API (safer than file copy)
        source = sqlite3.connect(str(db_path))
        dest = sqlite3.connect(str(backup_path))
        
        # Perform backup
        source.backup(dest)
        
        dest.close()
        source.close()
        
        # Verify backup is valid
        verify_backup(backup_path)
        
        print(f"[BACKUP] ✅ Backup successful: {backup_path}")
        
        # Cleanup old backups
        cleanup_old_backups(backup_dir, days=7)
        
    except Exception as e:
        print(f"[BACKUP] ❌ Backup failed: {e}")
        raise


def verify_backup(backup_path: Path):
    """Verify backup is a valid SQLite database"""
    conn = sqlite3.connect(str(backup_path))
    try:
        # Run integrity check
        result = conn.execute("PRAGMA integrity_check;").fetchone()
        if result[0] != "ok":
            raise ValueError(f"Backup integrity check failed: {result[0]}")
        
        # Verify operators table exists
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        
        if not any(t[0] == "operators" for t in tables):
            raise ValueError("Backup missing critical tables")
            
    finally:
        conn.close()


def cleanup_old_backups(backup_dir: Path, days: int = 7):
    """Remove backups older than specified days"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    for backup_file in backup_dir.glob("aos_backup_*.db"):
        # Extract timestamp from filename
        try:
            timestamp_str = backup_file.stem.replace("aos_backup_", "")
            file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
            if file_time < cutoff:
                print(f"[CLEANUP] Removing old backup: {backup_file}")
                backup_file.unlink()
                
        except (ValueError, OSError) as e:
            print(f"[CLEANUP] Warning: Could not process {backup_file}: {e}")


if __name__ == "__main__":
    backup_database()
