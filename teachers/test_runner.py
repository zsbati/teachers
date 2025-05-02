from django.test.runner import DiscoverRunner

class CustomTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_module = 'teachers_app'

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        import sys
        import os
        # Add the project root to PYTHONPATH
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

    def discover(self, start_dir=None, pattern=None, top_level_dir=None):
        if start_dir is None:
            start_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'teachers_app', 'tests')
        if top_level_dir is None:
            top_level_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return super().discover(start_dir=start_dir, pattern=pattern, top_level_dir=top_level_dir)
