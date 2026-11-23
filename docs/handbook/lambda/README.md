# Lambda Handbook

Theory and mental models for AWS Lambda (Day 4: serverless compute). Each chapter explains the concept, then points to lab code.

| # | Chapter | Question it answers |
|---|---------|---------------------|
| 1 | [Execution model](01-execution-model.md) | What is a handler? Cold vs warm starts, limits, memory vs CPU. |
| 2 | [Zip deploy to Floci](02-zip-deploy.md) | How do I package, deploy, invoke, and read the result (and errors)? |

## Roadmap mapping

| Roadmap item | Chapter |
|--------------|---------|
| 4.1 Execution model | 1 |
| 4.2 Zip deploy to Floci | 2 |

## Code index

| Concept | Where to look |
|---------|---------------|
| First handler, cold/warm counters | `labs/lambdas/report_worker/handler.py` |
| Handler with logic and error handling | `labs/lambdas/calculator/handler.py` |
| Call a handler locally with a fake context | `labs/lambdas/local_invoke.py` |
| Invoke the deployed function with boto3 | `labs/lambdas/invoke_demo.py` |
| Role trust policy | `labs/lambdas/trust-policy.json` |
