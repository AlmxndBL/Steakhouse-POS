import unittest
import sys
import os

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from tests.database_safety import require_isolated_test_database

# This legacy suite writes fixtures and exercises checkout. Refuse to import
# application/database modules until the isolated test endpoint is confirmed.
require_isolated_test_database()

# Ensure app root is in sys.path
# The application modules now live under app/, while their internal imports
# intentionally remain package-oriented (database, services, views, utils).
APP_PACKAGE_ROOT = os.path.join(APP_ROOT, "app")
if APP_PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, APP_PACKAGE_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_sandbox_tests():
    from database.seed import seed_data
    seed_data()

    print("=" * 60)
    print("  RUNNING STEAKHOUSE POS AUTOMATED SANDBOX TEST SUITE")
    print("=" * 60)
    
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=os.path.join(APP_ROOT, "tests"),
        pattern="test_*.py",
        top_level_dir=APP_ROOT
    )
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"  TEST SUMMARY: Ran {result.testsRun} tests")
    print(f"  Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("  ALL SANDBOX VERIFICATION TESTS PASSED 100%!")
        return 0
    else:
        print("  SOME TESTS FAILED!")
        return 1

if __name__ == '__main__':
    sys.exit(run_sandbox_tests())
