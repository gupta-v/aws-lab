"""
Get the local AWS emulator ready. Resources (buckets, tables) are created by the setup_*_lab.py scripts.

    uv run -m setup.floci            # start Floci with persistence + UI in your region
    uv run -m setup.floci --no-ui    # only start Floci

What it does:
  1. Starts Floci with --persist so data survives restarts (skips if already running)
  2. Replaces Floci's UI container with one that uses YOUR region (from AWS_DEFAULT_REGION)
"""
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx

import utils  # noqa: F401  (loads .env)

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
PERSIST_DIR = Path(__file__).parent.parent / "floci-data"
UI_NAME = "floci-ui"
FLOCI_UI_DEFAULT_NAME = "floci-aws-ui"   # the UI container Floci starts itself


def run(cmd):
    """Run a command; stop the script with its error message if it fails."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ {' '.join(cmd)}\n{result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def floci_is_up():
    try:
        return httpx.get(ENDPOINT, timeout=2).status_code < 500
    except httpx.HTTPError:
        return False


def start_floci():
    print("\n▶ Floci emulator")
    if floci_is_up():
        print(f"  ✓ already running at {ENDPOINT}")
        print("    (to enable persistence on an old session: floci stop, then re-run this)")
        return
    PERSIST_DIR.mkdir(exist_ok=True)
    print(f"  starting with persistence in {PERSIST_DIR} …")
    run(["floci", "start", "--persist", str(PERSIST_DIR)])
    for _ in range(30):
        if floci_is_up():
            print(f"  ✓ ready at {ENDPOINT}")
            return
        time.sleep(1)
    print("  ✗ Floci did not become ready. Try: floci logs")
    sys.exit(1)


def fix_ui_region():
    print(f"\n▶ Floci UI in region {REGION}")
    existing = run(["docker", "ps", "-a", "--format", "{{.Names}}"]).splitlines()
    for name in (FLOCI_UI_DEFAULT_NAME, UI_NAME):
        if name in existing:
            run(["docker", "rm", "-f", name])
    run([
        "docker", "run", "-d", "--name", UI_NAME, "-p", "4500:4500",
        "-e", "FLOCI_ENDPOINT=http://host.docker.internal:4566",
        "-e", f"AWS_REGION={REGION}",
        "-e", "AWS_ACCESS_KEY_ID=test",
        "-e", "AWS_SECRET_ACCESS_KEY=test",
        "floci/floci-ui:latest",
    ])
    print("  ✓ UI at http://localhost:4500")


if __name__ == "__main__":
    print(f"Endpoint: {ENDPOINT} | Region: {REGION}")
    start_floci()
    if "--no-ui" not in sys.argv:
        fix_ui_region()
    print("\nFloci ready ✅  Next: uv run -m setup.s3_lab / setup.ddb_lab")