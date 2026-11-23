# 2. Zip deploy to Floci

## Flow

1. Write `handler.py` (dependency-free, so the zip holds one file).
2. Zip it with the file at the **root** of the archive.
3. Create an IAM role Lambda can assume.
4. `create-function`, then `invoke`.

Run from the repo root with Floci up (`uv run setup/floci.py`). `AWS_ENDPOINT_URL` in `.env` points the CLI at Floci; with it unset these commands hit **real AWS**.

## 1. Package

```powershell
Compress-Archive -Path labs/lambdas/report_worker/handler.py -DestinationPath build/report_worker.zip -Force
```

`handler.py` must sit at the zip root, not in a subfolder, or `handler.handler` won't resolve. Dependencies would be installed next to it with `pip install -t` before zipping.

## 2. Role

A function needs an **execution role** that lets the Lambda service assume it (`labs/lambdas/trust-policy.json`). Permissions to call other services (S3, DynamoDB) get attached to this role later. Capture the ARN in a variable, since `create-function` needs it:

```powershell
$ROLE = aws iam create-role --role-name lambda-role `
  --assume-role-policy-document file://labs/lambdas/trust-policy.json `
  --query Role.Arn --output text
$ROLE
```

## 3. Create the function

```powershell
aws lambda create-function `
  --function-name report-worker `
  --runtime python3.14 `
  --handler handler.handler `
  --role $ROLE `
  --zip-file fileb://build/report_worker.zip

aws lambda wait function-active-v2 --function-name report-worker
```

`fileb://` (binary) is required for the zip. The `wait` blocks until the function is `Active`; invoking before that can fail. After a code change, redeploy with `aws lambda update-function-code --function-name report-worker --zip-file fileb://build/report_worker.zip`.

## 4. Invoke and read the response

```powershell
aws lambda invoke --function-name report-worker `
  --cli-binary-format raw-in-base64-out `
  --payload file://build/calc-event.json build/out.json
Get-Content build/out.json
```

The terminal shows only metadata (`StatusCode`, `FunctionError`); the handler's return value is written to `out.json`. From Python: `labs/lambdas/invoke_demo.py` (`boto3.client("lambda").invoke(...)`; read `r["Payload"]`).

Test the handler without any AWS: `uv run labs/lambdas/local_invoke.py` fakes the `context`.

## `StatusCode 200` does not mean success

`StatusCode` only says the **invoke call** worked. If your code raises, you still get `200`, plus a `FunctionError: Unhandled` header and an error object as the payload:

```
StatusCode=200  FunctionError=Unhandled
{"errorMessage": "Cannot divide or modulo by zero.", "errorType": "ValueError", "stackTrace": [...]}
```

Both kinds of failure return 200:

| Handler behaviour | `FunctionError` | Payload |
|-------------------|-----------------|---------|
| Raises (uncaught) | `Unhandled` | `errorMessage`, `errorType`, `stackTrace` |
| Catches and returns `{"status": "JOB_FAILED"}` | none | your own dict |

So callers must check `FunctionError`, and also your own `status` field if you catch errors. `uv run labs/lambdas/invoke_demo.py --fail` shows it (it needs a handler without the try/except deployed). Catching is right for *expected* failures (bad input); let *unexpected* ones raise so Lambda records the failure and async retries or dead-letter queues kick in.

## Logs

`print()` goes to CloudWatch Logs (`/aws/lambda/<name>`), including the `INIT:` line on cold starts. Each invoke also gets a request id, which is the thing to search for when debugging.

## Key takeaways

- Zip = code at the archive root + handler string `file.function` + execution role.
- `invoke` writes the result to a file; `StatusCode` 200 only means the call was delivered.
- Check `FunctionError`; uncaught exceptions surface there, caught ones don't.
- Redeploy code changes with `update-function-code`.
