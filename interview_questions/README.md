# Terraform Interview Challenge - Solutions

## Overview

| Challenge | Focus | Key Services |
|-----------|-------|--------------|
| 1 | S3 Basics | S3 |
| 2 | IAM & Access Control | IAM, S3 Bucket Policy |
| 3 | Event-Driven Data Pipeline | S3, SQS, EventBridge, Step Functions, Lambda, SNS |
| 4 | NFL Scoreboard App | S3, API Gateway, Lambda, DynamoDB |

---

## Callouts

| Practice | Where |
|----------|-------|
| `default_tags` in provider | All challenges — Environment, ManagedBy |
| File organization | Separate files per service (s3.tf, iam.tf, lambda.tf) |
| Least privilege IAM | Scoped to specific resources |
| `data` blocks for policies | `aws_iam_policy_document` over inline JSON for challenge 3+4 |

---

---

## Challenge 1: S3 Bucket

**Objective:** Create an S3 bucket named `ncaa` with force destroy enabled.

**Approach:** Single resource, minimal config.
```hcl
resource "aws_s3_bucket" "ncaa" {
  bucket        = "ncaa"
  force_destroy = true
}
```

---

## Challenge 2: IAM & Access Control

**Objective:** Create read-only user, read/write role, and encryption enforced bucket policy.

**Approach:**
- Separate IAM statements for bucket-level (`s3:ListBucket`) vs object-level (`s3:GetObject`) permissions
- Managed policies over inline for auditability
- Bucket policy with `StringNotEquals` condition to deny unencrypted uploads (and null condition)

**Key Resources:**
- `aws_iam_user` — ncaa-analyst
- `aws_iam_role` — ncaa-data-writer
- `aws_iam_policy` — Read-only and read/write policies
- `aws_s3_bucket_policy` — Deny PutObject without AES256

---

## Challenge 3: Event-Driven Data Pipeline

**Objective:** Process files as they arrive in S3, buffer via SQS, batch-process on a schedule, and notify on completion.

### Architecture
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   Files arrive (sporadic, burst, ...adaptable)                                          │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────┐      ┌─────────┐      ┌──────────────────────────────────┐    │
│   │   S3    │─────►│   SQS   │─────►│  EventBridge (every 5 min)       │    │
│   │         │      │ (buffer)│      │  "If queue has messages, start"  │    │
│   └─────────┘      └─────────┘      └───────────────┬──────────────────┘    │
│                                                     │                       │
│                                                     ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Step Functions                                                     │   │
│   │                                                                     │   │
│   │  ┌──────────────┐                                                   │   │
│   │  │ Drain Queue  │  Lambda: pull all messages from SQS               │   │
│   │  └──────┬───────┘                                                   │   │
│   │         │                                                           │   │
│   │         ▼                                                           │   │
│   │  ┌──────────────────────────────────────┐                           │   │
│   │  │  Map State (parallel, per file)      │                           │   │
│   │  │  ├── Process game_001.json           │                           │   │
│   │  │  ├── Process game_002.json           │                           │   │
│   │  │  └── ... (up to 50 files)            │                           │   │
│   │  └──────────────────────────────────────┘                           │   │
│   │         │                                                           │   │
│   │         ▼                                                           │   │
│   │  ┌──────────────┐                                                   │   │
│   │  │   Notify     │  Single SNS: "50 files processed, 48 success"     │   │
│   │  └──────────────┘                                                   │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Ingestion | S3 event → SQS | Decouples file arrival from processing; handles bursts |
| Scheduler | EventBridge (every 5 min) | Polls queue on a schedule, only starts pipeline if messages exist |
| Orchestration | Step Functions | Fan-out parallelism, built-in retry, single notification after all complete |
| Compute | Lambda | Serverless, scales per-file in Map state |
| Notifications | SNS | Multi-channel, decoupled, single summary after batch |
| Error Handling | Retry + Catch | Automatic retry with backoff, route failures to notify |

### Trade-offs

- **SQS buffering vs direct S3 trigger:** SQS absorbs bursts and allows batch processing on a schedule rather than per-file Lambda invocations. Avoids thundering herd on large uploads.
- **Lambda vs Fargate:** Lambda is simpler but 15-min limit. Fargate is cheaper for sustained compute but more setup.
- **Step Functions billing:** Standard workflows charge per transition, not duration — waiting is free.

---

## Challenge 4: NFL Scoreboard App

**Objective:** Real-time scoreboard with serverless API and WebSocket push updates.

### Architecture — REST + Polling (LocalStack compatible)
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Frontend (S3 Static Website)                             │  │
│  │  • Fetches data on load, polls every 5s                   │  │
│  └────────────────────────────┬──────────────────────────────┘  │
│                               │ HTTP (poll)                     │
│                               ▼                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  REST API Gateway                                         │  │
│  │                                                           │  │
│  │  GET /scores ─────► Lambda (get-scores) ──► DynamoDB      │  │
│  │                                             nfl-scores    │  │
│  │                                                           │  │
│  │  GET /standings ──► Lambda (get-standings) ► DynamoDB     │  │
│  │                                             nfl-standings │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture — WebSocket Real-Time Push (requires LocalStack Pro or AWS)
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  DynamoDB Tables                WebSocket API Gateway           │
│  ┌──────────────────┐          ┌──────────────────────────┐     │
│  │  nfl-scores       │          │  $connect    ► Lambda    │    │
│  │  nfl-standings    │          │  $disconnect ► Lambda    │    │
│  │  (streams on)     │          └─────────────▲────────────┘    │
│  └────────┬──────────┘                        │                 │
│           │ DynamoDB Stream                   │ post_to_connection
│           ▼                                   │                 │
│  ┌────────────────────────────────────────────┴──────────────┐  │
│  │  Lambda (ws_broadcast)                                    │  │
│  │  • Triggered by stream events (NEW_IMAGE)                 │  │
│  │  • Scans nfl-ws-connections for active clients            │  │
│  │  • Pushes changed data to all connected browsers          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  DynamoDB: nfl-ws-connections                                   │
│  • Stores connectionId on $connect, removes on $disconnect      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend | S3 static website | Simple, cheap, scales infinitely |
| Initial load | REST API | Full data fetch on page load; LocalStack free tier compatible |
| Real-time | WebSocket API + DynamoDB Streams | True push — no polling overhead, instant updates to all clients |
| Fallback | Polling (5s) | Auto-fallback if WebSocket unavailable (e.g., free LocalStack) |
| Database | DynamoDB (PAY_PER_REQUEST) + Streams | Key-value lookups, auto-scaling, streams trigger broadcast |
| Connection tracking | DynamoDB (nfl-ws-connections) | Simple connectionId store, scanned on broadcast |

### Trade-offs

- **Hybrid REST + WebSocket:** REST API handles initial page load and serves as fallback. WebSocket pushes real-time changes. This is more complex but gives the best UX.
- **WebSocket on LocalStack:** Free LocalStack doesn't support API Gateway v2 (WebSocket). The Terraform will plan successfully but apply requires LocalStack Base or real AWS. Frontend falls back to polling automatically.
- **REST vs HTTP API:** Had to use REST API with free version of LocalStack. HTTP API would be cheaper/faster in prod.
- **CloudFront:** Not included for simplicity. In prod, add for HTTPS + CDN caching + WebSocket upgrade support.

### Testing

`tests/challenge_4/seed_data.py` seeds DynamoDB and runs a live game simulation:

1. Seeds 3 games (Chiefs/Ravens final, Cowboys/Eagles in Q4, 49ers/Rams upcoming) and 5 team standings
2. Counts down Q4 clock from 0:30 to 0:03 (1 update/second)
3. Cowboys score a touchdown — score goes to 20-21
4. Waits 8 seconds, then two-point conversion is good — final score 22-21
5. Updates standings: Cowboys 10-3, Eagles 9-4

```bash
source .venv/bin/activate
python tests/challenge_4/seed_data.py
```

With the frontend open in the browser, scores update in near real-time (5s polling or instant via WebSocket).

Ad-hoc DynamoDB updates can also be made via CLI:
```bash
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 \
aws --endpoint-url=http://localhost:4566 dynamodb update-item \
  --table-name nfl-scores \
  --key '{"gameId":{"S":"game-002"}}' \
  --update-expression "SET homeScore = :score, #s = :status" \
  --expression-attribute-names '{"#s":"status"}' \
  --expression-attribute-values '{":score":{"N":"28"},":status":{"S":"Final"}}'
```

---

## CI/CD — GitHub Actions

Two workflows run all challenges against LocalStack in CI. Same as local.

| Workflow | Trigger | Environment | Actions |
|----------|---------|-------------|---------|
| `deploy-dev.yml` | PR to `main` | dev | Plan → Comment on PR → Apply → Smoke Tests → Comment Success |
| `deploy-prod.yml` | Push to `main` | prod | Plan (with `-out`) → Apply → Smoke Tests |

### How It Works

- **LocalStack** runs as a GitHub Actions service container (privileged, with Docker socket mounted for Lambda execution)
- **Matrix strategy** runs all 4 challenges in parallel
- **Environment** is parameterized via `terraform -var="environment=dev|prod"` (not hardcoded in `.tf` files)
- **Lambda zip** is built in CI before terraform runs (challenges 3 & 4)

### Smoke Tests

After `terraform apply`, each challenge runs verification:

All challenges use `pytest tests/test_challenge_$N.py -v`:

| Challenge | Test |
|-----------|------|
| 1 | `pytest tests/test_challenge_1.py` — verifies S3 bucket `ncaa` exists |
| 2 | `pytest tests/test_challenge_2.py` — IAM user `ncaa-analyst`, role `ncaa-data-writer`, policy actions (read-only vs read-write), resource scoping to `ncaa` bucket, policy attachments, trust policy (EC2), bucket policy denies unencrypted uploads |
| 3 | `pytest tests/test_challenge_3.py` — S3 bucket, SQS queue, Step Functions state machine, SNS topic, Lambda functions (`drain-queue`, `process-file`, `notify`), EventBridge rule; end-to-end: S3 upload → SQS message delivery → Step Functions execution |
| 4 | `pytest tests/test_challenge_4.py` — S3 bucket with `index.html` (API URL injected), DynamoDB tables with streams enabled, Lambda functions (`get-scores`, `get-standings`), REST API; end-to-end: seeds data, hits `/scores` and `/standings` endpoints, validates response format |
