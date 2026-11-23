# 3. Config: env vars, timeouts, memory

Settings that decide cost and reliability. They live on the **function**, not in the zip, so changing them needs no new code. All commands are PowerShell, run from the repo root with Floci up.

## Environment variables

Set per function; Lambda hands them to your code as `os.environ`. Values are always **strings**, so convert them.

```python
PRECISION = int(os.environ.get("PRECISION", "2"))                    # env vars are strings
FUNCTION_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "local")   # set by AWS, not you
```

Read them at **module level** (init), once per environment. The handler uses `PRECISION` as the default and lets the event's `precision` override it.

Gotcha: `--environment` **replaces the whole set**. To add one variable you must resend the others, or they disappear.

```powershell
aws lambda update-function-configuration --function-name calculator-worker `
  --environment "Variables={LOG_LEVEL=debug}"          # now PRECISION is gone

aws lambda update-function-configuration --function-name calculator-worker `
  --environment "Variables={PRECISION=4,LOG_LEVEL=debug}"
```

An env-var change makes Lambda create fresh environments, so the next invoke is cold and re-reads the values. Example: `PRECISION=4` gives `3.3333` for `10 / 3`, and `PRECISION=1` gives `3.3`.

## Timeout and memory

```powershell
aws lambda update-function-configuration --function-name calculator-worker `
  --timeout 30 --memory-size 256 --environment "Variables={PRECISION=4}"

aws lambda wait function-updated-v2 --function-name calculator-worker
```

Always **wait** after a configuration update (see chapter 2): until the update finishes, invokes can hit the old settings or fail with a conflict.

Confirm what is deployed:

```powershell
aws lambda get-function-configuration --function-name calculator-worker `
  --query "{Timeout:Timeout,Memory:MemorySize,Env:Environment}"
```

- **Timeout** (default 3 s, max 900 s): the cap on one invoke. Set it just above the real worst case; a huge timeout hides hangs and costs money.
- **Memory** (128 MB to 10,240 MB): also sets CPU and the price per millisecond (chapter 1).

The context object shows the effective values: `memory_mb` and `time_left_ms` in the response (30 s timeout gives about 24,998 ms left after a 5 s sleep).

## Seeing a timeout on purpose

The handler sleeps for `delay_s` seconds. Under the 30 s timeout a 5 s sleep succeeds:

```powershell
'{"job_id":"j1","input_a":10,"input_b":3,"operation":"div","delay_s":5}' | Set-Content build/calc-event.json
aws lambda invoke --function-name calculator-worker --payload fileb://build/calc-event.json build/out.json
Get-Content build/out.json
```

A 35 s sleep outlives the timeout, so Lambda kills the invoke. `--log-type Tail` returns the last 4 KB of the log base64-encoded; decode it to see the platform's message:

```powershell
'{"job_id":"j2","input_a":10,"input_b":3,"operation":"div","delay_s":35}' | Set-Content build/calc-event.json
$log = aws lambda invoke --function-name calculator-worker --payload fileb://build/calc-event.json `
  --log-type Tail --query LogResult --output text build/out.json
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($log))
Get-Content build/out.json
```

Expected: `StatusCode 200` again (see chapter 2), a `FunctionError`, and `Task timed out after 30.00 seconds` in the output. The code never reaches its `return`, and `try/except` in your handler cannot catch it, because Lambda stops the process from outside. Check `time_left_ms` or `context.get_remaining_time_in_millis()` before slow work and exit cleanly if there is not enough time.

Then a normal event, without `delay_s`, to confirm recovery (the handler's default delay is 2 s):

```powershell
'{"job_id":"j3","input_a":10,"input_b":3,"operation":"div"}' | Set-Content build/calc-event.json
aws lambda invoke --function-name calculator-worker --payload fileb://build/calc-event.json build/out.json
Get-Content build/out.json
```

## Redeploying code (used along the way)

```powershell
Compress-Archive -Path labs/lambdas/calculator/handler.py -DestinationPath build/calculator_worker.zip -Force
tar -tf build/calculator_worker.zip        # check handler.py is at the zip root
aws lambda update-function-code --function-name calculator-worker --zip-file fileb://build/calculator_worker.zip
aws lambda wait function-updated-v2 --function-name calculator-worker
```

Code and configuration are separate updates; a code deploy does not change env vars, timeout or memory.

## Key takeaways

- Env vars are per-function strings; `--environment` replaces the whole set.
- `update-function-configuration`, then `wait function-updated-v2`, then verify with `get-function-configuration`.
- A timeout is a hard kill: no exception, no `except`, still HTTP 200 with a function error.
- Timeout caps duration; memory sets CPU and cost.
