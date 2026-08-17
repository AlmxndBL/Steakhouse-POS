import os
import sqlite3
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional

class BackupService:
    @staticmethod
    def get_default_db_path() -> str:
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pos_data.db")

    @staticmethod
    def get_default_backup_dir() -> str:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @classmethod
    def create_backup(
        cls,
        db_path: Optional[str] = None,
        backup_dir: Optional[str] = None,
        max_backups: int = 30
    ) -> str:
        """
        Performs a safe, non-blocking online backup of the SQLite database.
        Cleans up old backups keeping up to `max_backups`.
        """
        source_db = db_path or cls.get_default_db_path()
        target_dir = backup_dir or cls.get_default_backup_dir()

        if not os.path.exists(source_db):
            raise FileNotFoundError(f"Database file not found: {source_db}")

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pos_backup_{timestamp_str}.db"
        backup_filepath = os.path.join(target_dir, backup_filename)

        # Use SQLite Online Backup API for zero corruption & safe concurrency
        src_conn = sqlite3.connect(source_db)
        dst_conn = sqlite3.connect(backup_filepath)
        try:
            with dst_conn:
                src_conn.backup(dst_conn, pages=100)
        finally:
            dst_conn.close()
            src_conn.close()

        # Retention Cleanup
        cls._cleanup_old_backups(target_dir, max_backups=max_backups)

        return backup_filepath

    @classmethod
    def list_backups(cls, backup_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns a sorted list of existing backups (newest first)."""
        target_dir = backup_dir or cls.get_default_backup_dir()
        files = glob.glob(os.path.join(target_dir, "pos_backup_*.db"))
        files.sort(key=os.path.getmtime, reverse=True)

        backups = []
        for f in files:
            stat = os.stat(f)
            backups.append({
                "filename": os.path.basename(f),
                "filepath": f,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime)
            })
        return backups

    @classmethod
    def _cleanup_old_backups(cls, backup_dir: str, max_backups: int):
        files = glob.glob(os.path.join(backup_dir, "pos_backup_*.db"))
        files.sort(key=os.path.getmtime, reverse=True)
        if len(files) > max_backups:
            for old_file in files[max_backups:]:
                try:
                    os.remove(old_file)
                except Exception:
                    pass
