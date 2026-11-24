# Lambda Handbook

Theory and mental models for AWS Lambda (Day 4: serverless compute). Each chapter explains the concept, then points to lab code.

| # | Chapter | Question it answers |
|---|---------|---------------------|
| 1 | [Execution model](01-execution-model.md) | What is a handler? Cold vs warm starts, limits, memory vs CPU. |
| 2 | [Zip deploy to Floci](02-zip-deploy.md) | How do I package, deploy, invoke, and read the result (and errors)? |
| 3 | [Config: env vars, timeouts, memory](03-config.md) | What settings decide cost and reliability, and what does a timeout look like? |
| 4 | [Container images](04-container-images.md) | How do I ship heavy dependencies (FastAPI + LangChain) as an image, test it locally, and deploy it? |

## Roadmap mapping

| Roadmap item | Chapter |
|--------------|---------|
| 4.1 Execution model | 1 |
| 4.2 Zip deploy to Floci | 2 |
| 4.3 Config: env vars, timeouts, memory | 3 |
| 4.4 Container images | 4 |

## Code index

| Concept | Where to look |
|---------|---------------|
| First handler, cold/warm counters | `labs/lambdas/report_worker/handler.py` |
| Handler with logic and error handling | `labs/lambdas/calculator/handler.py` |
| Call a handler locally with a fake context | `labs/lambdas/local_invoke.py` |
| Invoke the deployed function with boto3 | `labs/lambdas/invoke_demo.py` |
| Role trust policy | `labs/lambdas/trust-policy.json` |
| Container image app (FastAPI + LangChain agent) | `labs/lambdas/info_buddy/` |
| Lambda entry point (Mangum) | `labs/lambdas/info_buddy/handler.py` |
| Lambda image build | `labs/lambdas/info_buddy/Dockerfile.lambda` |
| Deploy, update and scrub the key | `setup/info_buddy_lab.py` |
| Pre-commit guard against Groq keys | `.githooks/pre-commit` |
