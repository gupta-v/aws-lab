# 4. Container images

Package the function as a Docker image instead of a zip. Only the packaging changes: `handler(event, context)`, cold/warm starts, timeout, memory and env vars from chapters 1 to 3 are identical.

The lab app is **Info Buddy**: a FastAPI app with a LangChain agent (Groq model, tools: time, weather, web search), wrapped for Lambda with Mangum. Code: `labs/lambdas/info_buddy/`.

## Why containers

| | Zip (chapter 2) | Container image |
|---|---|---|
| Size limit | 250 MB unzipped | 10 GB |
| Python + OS | AWS supplies them | You build them in, from AWS's base image |
| Dependencies | Hard beyond simple pure-Python packages | `pip install` in a Dockerfile |
| Local test | Fake context | Run the real image locally |
| Deploy | Upload zip | Build image, push to ECR, point Lambda at it |

Choose a zip for small code with few pure-Python dependencies. Choose an image for heavy dependencies (LangChain, LangGraph, pandas, torch), system libraries, or when the team already ships Docker.

## What is inside a Lambda image

Start from AWS's base image, `public.ecr.aws/lambda/python:3.14`. It already has:

- **Python 3.14** on Amazon Linux.
- **Runtime Interface Client (RIC):** the bridge to Lambda. It fetches events, calls your handler and returns the result.
- **Runtime Interface Emulator (RIE):** pretends to be Lambda on your laptop.
- **`LAMBDA_TASK_ROOT`** (`/var/task`): where code and dependencies go. The RIC resolves the handler string against it.

Your Dockerfile adds three things: dependencies into `/var/task`, your code into `/var/task`, and `CMD ["file.object"]`. There is no uvicorn, no `EXPOSE`, no port: nothing listens, Lambda calls the handler.

## Why an adapter: Mangum

Lambda calls `handler(event, context)`; FastAPI expects HTTP. `handler.py` is the glue:

```python
from mangum import Mangum
from controllers.api import app

handler = Mangum(app, lifespan="off")
```

`Mangum` instances are callable. Mangum turns the API Gateway v2 event (`rawPath`, `requestContext.http.method`, `body` as a **string**) into an ASGI request, runs FastAPI, and turns the response into `{"statusCode", "headers", "body", "isBase64Encoded"}`. `body` is a string because real HTTP bodies are bytes. The app code is unchanged; it runs under uvicorn too.

`CMD ["handler.handler"]` means file `handler.py`, object `handler`. At INIT the RIC imports `handler.py`, which imports the app, which imports `core/agent.py` and builds the agent. That is why the cold start is slow, and why the agent is built at module level: once per environment, reused when warm.

## Project layout

```
labs/lambdas/info_buddy/
  core/agent.py          # LangChain agent + tools
  controllers/api.py     # FastAPI app: GET /health, POST /chat
  models/schema.py       # pydantic request/response models
  handler.py             # Mangum(app), the Lambda entry point
  Dockerfile             # plain image (uvicorn), a Day 11 preview
  Dockerfile.lambda      # Lambda image (base image + CMD handler.handler)
  events/*.json          # hand-written API Gateway v2 events for local tests
  pyproject.toml         # its own deps, so LangChain stays out of the repo root
  .env                   # GROQ_API_KEY, git-ignored
```

`controllers/api.py` inserts the app root into `sys.path` so `core` and `models` import from any working directory, following the repo convention.

## Commands used

Run from `labs/lambdas/info_buddy/` unless noted. Floci must be up for the deploy steps (`uv run setup/floci.py` from the repo root).

### 1. Project setup
```powershell
mkdir labs/lambdas/info_buddy
cd labs/lambdas/info_buddy
uv init --no-workspace --python 3.14
uv add fastapi uvicorn langchain langchain-groq mangum httpx ddgs
git check-ignore -v .env          # must print a rule, or the key could be committed
```
`uv init` makes a packaged project. This is an app, so delete the `[build-system]` and `[project.scripts]` sections from `pyproject.toml` and the generated `src/` folder.

### 2. Run locally, no Docker
```powershell
uv run --env-file .env uvicorn controllers.api:app --port 8000
curl.exe http://localhost:8000/health
curl.exe -X POST http://localhost:8000/chat -H "content-type: application/json" -d '{\"message\":\"weather in Pune?\"}'
```
Swagger UI is at `http://localhost:8000/docs`. An empty `message` returns 422 from pydantic before the agent runs.

### 3. Plain Docker image
```powershell
uv export --no-hashes --no-dev --no-emit-project -o requirements.txt
docker build -t info-buddy:local .
docker run --rm -p 8000:8000 --env-file .env info-buddy:local
docker history info-buddy:local --no-trunc     # confirm no GROQ in any layer
```
- The key goes in at `docker run --env-file`, never into the image: the image can be pushed or shared without leaking it, and the key can be rotated without a rebuild. `.dockerignore` excludes `.env`.
- uvicorn must listen on `--host 0.0.0.0`. On the default `127.0.0.1` it only listens on the container's own loopback: the port mapping connects, then the connection is dropped, and curl exits with **52, "Empty reply from server"**. There is no HTTP status at all, so it is not a 400 or 502 (those need a server or gateway that answered).

### 4. Lambda image
```powershell
docker build --platform linux/amd64 --provenance=false -f Dockerfile.lambda `
  -t 000000000000.dkr.ecr.ap-south-1.amazonaws.com/info-buddy:v1 .
```
- `FROM public.ecr.aws/lambda/python:3.14`
- `pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}`: dependencies sit next to the code, no virtualenv.
- `COPY` code and `handler.py` into `${LAMBDA_TASK_ROOT}`.
- `CMD ["handler.handler"]`.
- `--platform linux/amd64` avoids an arm image on an arm laptop (`exec format error`). `--provenance=false` stops Docker adding an attestation manifest, which real Lambda rejects.
- The ECR-shaped tag lets Floci find the image on the local Docker daemon, so no push is needed. Real AWS needs the image pushed to ECR in the same account and region.
- The image is about 1 GB uncompressed (the plain image is about 348 MB).

### 5. Test with the Runtime Interface Emulator (no Floci)
```powershell
docker run --rm -p 9000:8080 --env-file .env `
  000000000000.dkr.ecr.ap-south-1.amazonaws.com/info-buddy:v1
curl.exe -s -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d "@events/chat.json"
curl.exe -s -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" -d "@events/health.json"
```
`events/chat.json` is an API Gateway HTTP API (v2) event: `rawPath: "/chat"`, `requestContext.http.method: "POST"`, `body` as a JSON **string**. You play API Gateway by hand. The reply is `{"statusCode": 200, "body": "{\"reply\": ...}", ...}`. RIE does not enforce memory or timeout limits, so its `REPORT` line shows the emulator default memory and no real `Init Duration`.

### 6. Deploy to Floci
`setup/info_buddy_lab.py` does the deploy so the key is read from `labs/lambdas/info_buddy/.env` and never typed or stored in a script:
```powershell
uv run setup/info_buddy_lab.py             # create or update, tag v1
uv run setup/info_buddy_lab.py --tag v2    # point the function at another tag
uv run setup/info_buddy_lab.py --scrub     # blank the key before committing
```
The script uses boto3 and does the equivalent of:
```powershell
aws lambda create-function --function-name info-buddy --package-type Image `
  --code ImageUri=000000000000.dkr.ecr.ap-south-1.amazonaws.com/info-buddy:v1 `
  --role $ROLE --timeout 60 --memory-size 512 `
  --environment "Variables={GROQ_API_KEY=...}"
aws lambda wait function-active-v2 --function-name info-buddy
```
There is no `--runtime` and no `--handler`: the image already contains both. It reuses `lambda-role` (created in chapter 2), creating it if missing.

### 7. Invoke
```powershell
aws lambda invoke --function-name info-buddy `
  --payload fileb://labs/lambdas/info_buddy/events/chat.json build/out.json
Get-Content build/out.json
```
Run from the repo root. Needs `AWS_ENDPOINT_URL`, `AWS_DEFAULT_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` set in the session (the values in `.env`), or `--profile floci`. Put `--profile` on the `aws` command, and a PowerShell line-continuation backtick must be the very last character on its line.

### 8. Cold vs warm
`--log-type Tail` and CloudWatch Logs showed no usable output for this image function on Floci (details below), so the cold start was measured from the client with a redeploy first (forces a new environment):

| Call | Time |
|---|---|
| chat, cold | 5.15 s |
| chat, warm | 2.50 s, 2.39 s |
| health, warm | 0.01 s, 0.06 s |

The cold call cost about 2.7 s more: INIT imports FastAPI, LangChain, Groq and `ddgs` and builds the agent. The warm 2.4 s is the model call and weather lookup. `/health` shows Lambda plus Mangum overhead is tens of milliseconds. One cold sample, timed from the client, so this shows the pattern, not exact numbers.

To shrink INIT: lazy-import heavy libraries, trim dependencies, use a smaller image, provisioned concurrency on real AWS (INIT already done).

### 9. Function URL
```powershell
aws lambda create-function-url-config --function-name info-buddy --auth-type NONE
aws lambda add-permission --function-name info-buddy --statement-id url-public `
  --action lambda:InvokeFunctionUrl --principal "*" --function-url-auth-type NONE
curl.exe <FunctionUrl>health
curl.exe -X POST <FunctionUrl>chat -H "content-type: application/json" -d '{\"message\":\"weather in Pune?\"}'
```
On Floci the URL looked like `http://<id>.lambda-url.ap-south-1.localhost:4566/`. `NONE` means anyone with the URL can call the function and spend your Groq quota. On real AWS a `NONE` URL also needs the `add-permission` policy, or it returns 403 (Floci accepted it; I did not test whether it enforces it). The Function URL builds the API Gateway v2 event for you, the same shape as the hand-written one. API Gateway adds routing across functions, API keys and usage plans, request validation, throttling, custom domains and caching (Day 7).

### 10. Ship a change
```powershell
docker build --platform linux/amd64 --provenance=false -f Dockerfile.lambda `
  -t 000000000000.dkr.ecr.ap-south-1.amazonaws.com/info-buddy:v2 .
uv run setup/info_buddy_lab.py --tag v2     # update-function-code + wait function-updated-v2
```
Test change: `/health` gained `"version": "v2"`. After building `:v2` but before updating, the live function still answered without `version`: building changes nothing in Lambda. After the update it showed `{"status":"ok","version":"v2"}`.

## Breaking it on purpose

| Break | What happened |
|---|---|
| Timeout set to 1 s | Function URL `POST /chat`: **HTTP 502**, empty body. Direct invoke: `StatusCode 200`, `FunctionError: Unhandled`, `Task timed out after 1 seconds` (`Function.TimedOut`). `/health` still worked because it takes milliseconds. A timeout is a hard kill: `try/except` can't catch it. |
| `body` as a JSON object instead of a string | `FunctionError: Unhandled`, `AttributeError: 'dict' object has no attribute 'encode'`, raised inside `mangum/handlers/api_gateway.py`. FastAPI never ran. A Function URL always sends a string, so only hand-written events hit this. |

Not run (expected, not observed here): same-tag rebuild without `update-function-code` (real AWS locks the image digest, so nothing changes; Floci may differ), and removing `GROQ_API_KEY`. Importing the app without the key fails immediately, because the agent is built at import: a missing key is an INIT failure, not a failure on the first request.

## Gotchas

| Gotcha | What happens | Fix |
|---|---|---|
| New image under the same tag | Lambda locks onto the image **digest** when you create or update; a new push under the same tag changes nothing | `update-function-code` after every build; use versioned tags (`:v1`, `:v2`), not `:latest` |
| CPU architecture mismatch | arm64 build, x86_64 function: `exec format error` | `--platform linux/amd64` (or set the function to arm64) |
| Provenance attestation | Real Lambda rejects the manifest ("image manifest not supported") | `--provenance=false` |
| Code outside `/var/task` | `ImportModuleError` | copy to `${LAMBDA_TASK_ROOT}` |
| Big images | Bigger downloads, slower cold starts | slim dependencies, multi-stage builds, no tests or caches in the image |
| Layers | Container functions can't use Lambda layers | everything goes into the image |

## Logs on Floci

- **Real AWS:** `aws logs tail /aws/lambda/info-buddy --follow` shows everything, including the `REPORT` line with `Init Duration`.
- **Floci, this image function:** the log group has streams but **0 events**; `--log-type Tail` returned an unreadable `LogResult` (boto3 returned none); `docker logs` on the function's own container (`floci-aws-info-buddy-<id>`) was empty.
- **What does work:**
  ```powershell
  docker logs floci 2>&1 | Select-String "info-buddy"
  ```
  gives one line per invocation (`Lambda URL invocation: POST ... -> info-buddy`) and a `Created log stream` line for each new container (a cold start). For your own app's output, use the RIE container from step 5 and read `docker logs`.

## Keeping the Groq key out of git (temporary)

Floci persists function config, including env vars, in `floci-data/lambda-functions.json`, which is committed on purpose. So the key sits in that file while the function is deployed. Before any commit:

1. `uv run setup/info_buddy_lab.py --scrub` (sets the key to `REDACTED` through the API).
2. `floci stop`.
3. Commit.

`.githooks/pre-commit` blocks any staged change containing `gsk_...`. It is enabled with `git config core.hooksPath .githooks`, which must be run once on each workstation. Never bypass it with `--no-verify`. Day 6 replaces this with Secrets Manager so the key stays out of function config.

## Key takeaways

- An image is the AWS base image, your dependencies, your code in `/var/task`, and `CMD ["handler.handler"]`.
- A cold start does not build or install anything: it pulls the finished image and runs INIT (your imports). Building happens once, on your machine.
- Mangum adapts the Lambda event to FastAPI; the same app runs under uvicorn and Lambda.
- Update explicitly after every new image, with versioned tags. Build for `linux/amd64` with `--provenance=false`.
- Test locally with RIE; deploy to Floci with an ECR-shaped tag, no push. Real AWS needs ECR.
- Cold start costs INIT; warm calls cost only the work. Smaller images and lighter imports shrink it.
- A timeout is an unhandled error; the Function URL turns it into a 502 with no detail.
