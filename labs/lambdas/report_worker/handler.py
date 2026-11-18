"""
Report worker: our first Lambda function (deployed as a zip in 4.2).

AWS handler string: handler.handler  ->  file handler.py, function handler()
Keep this file dependency-free: the zip contains only this file.
"""
import time

# ── INIT: module level runs once per execution environment (cold start) ──
INIT_AT = time.time()
invocations = 0  # demo only: survives warm invokes. Never keep per-user data here.
print("INIT: new execution environment")


# ── INVOKE: runs on every request ──
def handler(event, context):
    global invocations
    invocations += 1
    cold = invocations == 1
    print(f"INVOKE #{invocations} cold={cold} request_id={context.aws_request_id}")

    return {
        "job_id": event.get("job_id", "unknown"),
        "status": "REPORT_READY",
        "cold_start": cold,
        "invocations_in_this_env": invocations,
        "env_age_s": round(time.time() - INIT_AT, 1),
        "memory_mb": context.memory_limit_in_mb,
        "time_left_ms": context.get_remaining_time_in_millis(),
    }