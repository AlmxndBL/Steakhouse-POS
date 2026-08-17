import unittest
import sys
import os

# Ensure app root is in sys.path
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

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
