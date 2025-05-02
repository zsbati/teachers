import os
import sys
import unittest
from django.test.utils import setup_test_environment
from django import setup

# Add the project root to PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teachers.settings')
setup()
setup_test_environment()

# Run tests
def run_tests():
    test_suite = unittest.TestLoader().discover('teachers_app/tests', pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(not success)
