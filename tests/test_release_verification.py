import os
import tempfile
import unittest

from database.connection import DATABASE_URL
from services.backup_service import BackupService


class TestReleaseVerification(unittest.TestCase):
    def test_postgresql_backup_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            backup = BackupService.create_backup(database_url=DATABASE_URL, backup_dir=directory)
            self.assertTrue(os.path.isfile(backup))
            self.assertGreater(os.path.getsize(backup), 0)
            self.assertEqual(BackupService.list_backups(directory)[0]["filepath"], backup)


if __name__ == "__main__":
    unittest.main()
