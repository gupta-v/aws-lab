# 1. Execution model

## What Lambda is

You upload a function; AWS runs it **only when an event arrives**, scales the number of copies automatically, and bills per request and per millisecond. No servers to manage, nothing running (or billed) while idle.

## Handler and event

Lambda calls one function you name, the **handler**:

```python
def handler(event, context): ...
```

- `event`: the input, a dict (already JSON-decoded). Its shape depends on the caller: whatever you pass to `invoke`, or an S3/SQS/API Gateway event later.
- `context`: runtime info: `aws_request_id`, `memory_limit_in_mb`, `get_remaining_time_in_millis()`.
- Return value: JSON-serialisable; it becomes the response of a synchronous invoke.

The **handler string** `handler.handler` means file `handler.py`, function `handler`.

## Execution environments: cold vs warm

Lambda runs your code inside an **execution environment** (a small sandbox).

- **Cold start**: no environment is free, so Lambda creates one, loads your code and runs the **init** code (everything at module level). Costs extra latency.
- **Warm start**: a finished environment is **reused** for the next request. Init is skipped; only the handler runs.

Lifecycle: **INIT** (create environment, download code, start Python, run module-level code) -> **INVOKE** (handler, every request) -> **freeze** between requests (memory, globals and `/tmp` are kept) -> **SHUTDOWN** after sitting idle for a while (AWS decides how long).

Cold start = INIT + INVOKE; warm = INVOKE only. Since 1 Aug 2025 the INIT phase is **billed** for all configurations, zip included, so keep INIT light (heavy imports like LangGraph hurt both latency and cost).

```python
INIT_AT = time.time()   # init: once per environment
invocations = 0

def handler(event, context):   # invoke: every request
    global invocations
    invocations += 1
```

Three sequential invokes of the lab function give `cold_start` true, false, false and `invocations_in_this_env` 1, 2, 3. The counter survives because the same environment served all three.

Consequences:

- Put expensive setup (boto3 clients, config, model loading) at **module level** so warm calls reuse it.
- **Never keep per-user data in globals**: the next request may reuse the environment, or land in a different one.
- Warm state is a cache, not storage; anything that must survive goes to DynamoDB or S3. Never rely on a warm environment existing. Idle environments are discarded after minutes, and parallel requests each get their own, each cold.
- An environment handles one request at a time; concurrent requests never share one.

## Limits to know

| Limit | Value |
|-------|-------|
| Timeout | 1 s to **15 min** (default 3 s) |
| Memory | 128 MB to 10 GB (default 128 MB) |
| Zip size | 50 MB zipped (direct upload), 250 MB unzipped including layers; larger code needs a container image (up to 10 GB) |
| Sync payload | 6 MB request / 6 MB response |
| Async payload | 1 MB |
| `/tmp` storage | 512 MB default, up to 10 GB; not shared between environments |
| Concurrency | 1000 per region by default (account-level, raisable) |

Timeout and the payload sizes are hard limits; memory-related and concurrency quotas can be raised on request. Source: the Lambda quotas page.

## Memory also buys CPU

You choose only memory (128 MB to 10,240 MB, 1 MB steps); **CPU scales proportionally** (about one vCPU at 1,769 MB). Billing is GB-seconds (memory x time), so more memory can cost *less* if a CPU-bound job (parsing, embeddings) finishes much faster. It does not help I/O-bound work such as waiting on an LLM API. Tune by measuring, not guessing.

## Sync vs async invoke

- **Synchronous** (`RequestResponse`): caller waits for the result and handles retries (CLI, API Gateway: "get job status").
- **Asynchronous** (`Event`): Lambda queues it and returns 202 at once, and the return value is discarded; failures are retried by Lambda (twice by default) (S3 upload: "start report"). Retries mean **duplicates are possible**, so handlers should be idempotent (see DynamoDB chapter 5).

## Check yourself

1. Invoked 3 times, 2 s apart: how many cold starts? **1**.
2. 3 invocations at the same instant: **3** cold starts, one environment per concurrent request.
3. A global `current_user = event["user_id"]` that the next request forgets to set: it sees the **previous user's id**, a data-leak bug.
4. 40 s LLM call, slow first request after a quiet period: cold start. Reduce it with lighter INIT (lazy or fewer imports), a smaller package, provisioned concurrency. More memory helps only the CPU-bound part of INIT, not the LLM wait.

## Key takeaways

- Handler = `(event, context)`; init code runs once per environment, handler on every request.
- Cold start = new environment; warm = reuse. Cache setup at module level, never user data.
- Hard limits: 15 min, 10 GB memory, 6 MB sync / 1 MB async payload, 250 MB unzipped code. Pass S3 keys, not report bodies.
- Memory sets CPU too.
