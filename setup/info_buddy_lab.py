"""
Deploy the info-buddy container image to Floci, with the Groq key read from its .env.

    uv run setup/info_buddy_lab.py            # create or update the function (tag v1)
    uv run setup/info_buddy_lab.py --tag v2   # deploy another image tag
    uv run setup/info_buddy_lab.py --scrub    # blank the key in the function config BEFORE you commit

Floci persists function config (including env vars) in floci-data/, which is committed.
Always run --scrub, stop Floci, then commit. The pre-commit hook blocks keys starting with gsk_.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3  # noqa: E402

import utils  # noqa: E402,F401  (loads root .env)

APP = Path(__file__).resolve().parent.parent / "labs" / "lambdas" / "info_buddy"
NAME, ROLE = "info-buddy", "lambda-role"
REGISTRY = "000000000000.dkr.ecr.ap-south-1.amazonaws.com/info-buddy"

lam, iam = boto3.client("lambda"), boto3.client("iam")


def groq_key():
    for line in (APP / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("GROQ_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("GROQ_API_KEY not found in labs/lambdas/info_buddy/.env")


def role_arn():
    try:
        return iam.get_role(RoleName=ROLE)["Role"]["Arn"]
    except iam.exceptions.NoSuchEntityException:
        trust = (APP.parent / "trust-policy.json").read_text()
        return iam.create_role(RoleName=ROLE, AssumeRolePolicyDocument=trust)["Role"]["Arn"]


def exists():
    try:
        lam.get_function(FunctionName=NAME)
        return True
    except lam.exceptions.ResourceNotFoundException:
        return False


def wait(waiter):
    lam.get_waiter(waiter).wait(FunctionName=NAME)


if "--scrub" in sys.argv:
    if exists():
        lam.update_function_configuration(FunctionName=NAME, Environment={"Variables": {"GROQ_API_KEY": "REDACTED"}})
        wait("function_updated_v2")
        print("✓ key blanked in", NAME)
    else:
        print("nothing to scrub: function does not exist")
    sys.exit()

tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "v1"
image = f"{REGISTRY}:{tag}"
env = {"Variables": {"GROQ_API_KEY": groq_key()}}

if exists():
    lam.update_function_code(FunctionName=NAME, ImageUri=image)
    wait("function_updated_v2")
    lam.update_function_configuration(FunctionName=NAME, Timeout=60, MemorySize=512, Environment=env)
    wait("function_updated_v2")
    print("✓ updated", NAME, "->", image)
else:
    lam.create_function(FunctionName=NAME, PackageType="Image", Code={"ImageUri": image}, Role=role_arn(),
                        Timeout=60, MemorySize=512, Environment=env)
    wait("function_active_v2")
    print("✓ created", NAME, "->", image)
