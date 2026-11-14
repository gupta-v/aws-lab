"""Load repo-root .env on first import of utils, so --env-file isn't needed."""
import os
from pathlib import Path

_env = Path(__file__).resolve().parent.parent / ".env"
if _env.is_file():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            # shortcut: no quote/export handling, upgrade to python-dotenv if .env gets fancy
            os.environ.setdefault(k.strip(), v.strip())
