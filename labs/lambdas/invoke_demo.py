"""
Invoke calculator-worker in Floci and show cold vs warm, and the "200 != success" gotcha.

    uv run labs/lambdas/invoke_demo.py            # 3 sequential invokes: #1 cold, #2/#3 warm
    uv run labs/lambdas/invoke_demo.py --fail     # b=0 invoke; needs the handler WITHOUT try/except deployed
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import boto3

import utils  # noqa: F401  (loads .env)

lam = boto3.client("lambda")
event = {"job_id": "j1", "user_id": "user1", "input_a": 6, "input_b": 3, "operation": "mul"}
if "--fail" in sys.argv:
    event.update(input_b=0, operation="div")

for i in range(1, 2 if "--fail" in sys.argv else 4):
    r = lam.invoke(FunctionName="calculator-worker", Payload=json.dumps(event))
    print(f"#{i} StatusCode={r['StatusCode']} FunctionError={r.get('FunctionError')}")
    print("   ", r["Payload"].read().decode())
