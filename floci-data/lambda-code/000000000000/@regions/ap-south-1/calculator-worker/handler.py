import operator

import time

import os

PRECISION = int(os.environ.get("PRECISION", "2"))                       # env vars are strings
FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local")      # set by AWS, not you
# ── INIT: module level runs once per execution environment (cold start) ──
INIT_AT = time.time()
invocations = 0  # demo only: survives warm invokes. Never keep per-user data here.
print("INIT: new execution environment")

def calculator(a: int, b: int, op: str):
    # Map operation names directly to functions
    operations = {
        "add": operator.add,  # or lambda x, y: x + y
        "sub": operator.sub,  # or lambda x, y: x - y
        "mul": operator.mul,  # or lambda x, y: x * y
        "div": operator.truediv,  # or lambda x, y: x / y
        "mod": operator.mod,  # or lambda x, y: x % y
    }

    # Check if the key exists in the dictionary (no brackets needed)
    if op in operations:
        if op in ("div", "mod") and b == 0:
            raise ValueError("Cannot divide or modulo by zero.")

        # Retrieve the function and call it with (a, b)
        resp = operations[op](a, b)
        return a, b, resp
    else:
        raise ValueError(f"Unsupported operation: '{op}'")

def handler(event, context):
    global invocations
    invocations += 1
    cold = invocations == 1
    print(f"INVOKE #{invocations} cold={cold} request_id={context.aws_request_id}")
    delay = event.get("delay_s", 2)
    a,b, operation= event.get("input_a"), event.get("input_b"), event.get("operation")
    if delay:
        print(f"before sleep: {context.get_remaining_time_in_millis()} ms left")
        time.sleep(delay)
        print(f"after sleep: {context.get_remaining_time_in_millis()} ms left")
    try:
        a, b, resp = calculator(a, b, operation)
        resp = round(resp, event.get("precision", 2))  # ints pass through unchanged
    except (ValueError, TypeError) as e:
        return {"job_id": event.get("job_id", "unknown"), "status": "JOB_FAILED", "error": str(e)}


    return {
        "job_id": event.get("job_id", "unknown"),
        "status": "JOB_DONE",
        "cold_start": cold,
        "response": f"The {operation} of {a} and {b} is {resp}",
        "invocations_in_this_env": invocations,
        "env_age_s": round(time.time() - INIT_AT, 1),
        "memory_mb": context.memory_limit_in_mb,
        "time_left_ms": context.get_remaining_time_in_millis(),
    }
