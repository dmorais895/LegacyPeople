"""Require the same Python minor version in Docker, CI, and local development."""

import sys

if sys.version_info[:2] != (3, 12):
    raise RuntimeError(
        "LegacyPeople requires Python 3.12. "
        "Create the local environment with python3.12 -m venv venv and activate it."
    )
