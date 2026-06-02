"""Entrypoint module for the Flask CLI.

Usage::

    flask --app app:create_app run --debug
"""

from creator_cv import create_app

app = create_app()
