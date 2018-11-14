#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")
    try:
        from configurations.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    include_coverage = 'include_coverage' in sys.argv
    if include_coverage:
        import coverage
        cov = coverage.coverage(source=['phi/views', '', 'phi/serializers', 'user_auth/views', 'user_auth/serializers'], omit=['*init__.py'], branch=True)
        cov.set_option('report:show_missing', True)
        cov.start()
        sys.argv.remove('include_coverage')
        execute_from_command_line(sys.argv)
        cov.stop()
        cov.save()
        cov.report()
    else:
        execute_from_command_line(sys.argv)
