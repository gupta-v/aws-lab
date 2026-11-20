"""
Call the handler on your machine, no AWS needed. Imitates what Lambda passes in.

    uv run labs/lambdas/local_invoke.py
"""
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from calculator.handler import handler


class FakeContext:
    """The few context attributes our handler uses."""
    def __init__(self, timeout_s=3, memory_mb=128):
        self.aws_request_id = str(uuid.uuid4())
        self.function_name = "report-worker"
        self.memory_limit_in_mb = memory_mb
        self._deadline = time.time() + timeout_s

    def get_remaining_time_in_millis(self):
        return int((self._deadline - time.time()) * 1000)


if __name__ == "__main__":
    event = {"user_id": "u1", "job_id": "job-001", "input_a": 10, "input_b": 0, "operation": "div"}
    for _ in range(3):
        print(handler(event, FakeContext()))