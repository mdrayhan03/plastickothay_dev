#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

    # `python manage.py runserver` (with no address) picks up RUN_PORT from .env, so the dev
    # port is configurable from the env file — no CLI arg or code change needed. An explicit
    # `runserver 8001` / `runserver 0.0.0.0:8001` still wins.
    if len(sys.argv) >= 2 and sys.argv[1] == "runserver":
        has_addr = any(a[:1].isdigit() or ":" in a for a in sys.argv[2:])
        if not has_addr:
            from dotenv import load_dotenv

            load_dotenv(Path(__file__).resolve().parent / ".env")
            run_port = os.getenv("RUN_PORT")
            if run_port:
                sys.argv.append(run_port)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
