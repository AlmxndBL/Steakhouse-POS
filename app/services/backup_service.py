import glob
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.connection import DATABASE_URL


class BackupService:
    """PostgreSQL logical backup service for the classroom deployment."""

    @staticmethod
    def get_default_backup_dir() -> str:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @classmethod
    def create_backup(cls, database_url: Optional[str] = None, backup_dir: Optional[str] = None, max_backups: int = 30) -> str:
        target_dir = backup_dir or cls.get_default_backup_dir()
        os.makedirs(target_dir, exist_ok=True)
        backup_path = os.path.join(target_dir, f"pos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dump")
        command = ["pg_dump", "--format=custom", "--no-owner", "--dbname", database_url or DATABASE_URL, "--file", backup_path]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as err:
            raise RuntimeError("pg_dump is required for PostgreSQL backups") from err
        except subprocess.CalledProcessError as err:
            raise RuntimeError(f"PostgreSQL backup failed: {err.stderr.strip()}") from err
        cls._cleanup_old_backups(target_dir, max_backups)
        return backup_path

    @classmethod
    def list_backups(cls, backup_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        target_dir = backup_dir or cls.get_default_backup_dir()
        files = sorted(glob.glob(os.path.join(target_dir, "pos_backup_*.dump")), key=os.path.getmtime, reverse=True)
        return [{"filename": os.path.basename(path), "filepath": path, "size_bytes": os.path.getsize(path), "created_at": datetime.fromtimestamp(os.path.getmtime(path))} for path in files]

    @classmethod
    def restore_backup(cls, backup_path: str, database_url: Optional[str] = None) -> str:
        if not os.path.isfile(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        command = ["pg_restore", "--clean", "--if-exists", "--no-owner", "--dbname", database_url or DATABASE_URL, backup_path]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except FileNotFoundError as err:
            raise RuntimeError("pg_restore is required for PostgreSQL restores") from err
        except subprocess.CalledProcessError as err:
            raise RuntimeError(f"PostgreSQL restore failed: {err.stderr.strip()}") from err
        return database_url or DATABASE_URL

    @staticmethod
    def _cleanup_old_backups(backup_dir: str, max_backups: int) -> None:
        files = sorted(glob.glob(os.path.join(backup_dir, "pos_backup_*.dump")), key=os.path.getmtime, reverse=True)
        for old_file in files[max_backups:]:
            try:
                os.remove(old_file)
            except OSError as err:
                logging.debug("Old backup cleanup skipped: %s", err)
