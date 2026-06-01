#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def _patch_drf_converter():
    """Prevent duplicate registration of drf_format_suffix converter."""
    try:
        import rest_framework.urlpatterns as _rfup
        _orig = _rfup.register_converter

        def _safe(converter, type_name):
            try:
                _orig(converter, type_name)
            except (ValueError, Exception):
                pass

        _rfup.register_converter = _safe
    except Exception:
        pass


def main():
    """Run administrative tasks."""
    _patch_drf_converter()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
