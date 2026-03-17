# Terraform Interview Challenge - Solutions

## Overview

| Challenge | Focus | Key Services |
|-----------|-------|--------------|
| 1 | S3 Basics | S3 |
| 2 | IAM & Access Control | IAM, S3 Bucket Policy |
| 3 | Scheduled Data Pipeline | EventBridge, Step Functions, Lambda, S3, SNS |
| 4 | NFL Scoreboard App | S3, API Gateway, Lambda, DynamoDB |

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

## Challenge 3: Scheduled Data Pipeline

**Objective:** Hourly job that processes files from S3 and notifies on completion/failure.

### Architecture
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   EventBridge (hourly)                                                  │
│         │                                                               │
│         ▼                                                               │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │  Step Functions                                                 │   │
│   │                                                                 │   │
│   │  ┌──────────────┐                                               │   │
│   │  │  List Files  │  Lambda (lightweight)                         │   │
│   │  └──────┬───────┘                                               │   │
│   │         │                                                       │   │
│   │         ▼                                                       │   │
│   │  ┌──────────────────────────────────────────┐                   │   │
│   │  │  Map State (parallel, per file)          │                   │   │
│   │  │  ├── Process File (game_001.json)        │  Lambda/Fargate   │   │
│   │  │  ├── Process File (game_002.json)        │  for data         │   │
│   │  │                                          │  transformations  │   │
│   │  │  • Retry 3x with backoff                 │                   │   │
│   │  └──────────────────────────────────────────┘                   │   │
│   │         │                                                       │   │
│   │         ▼                                                       │   │
│   │  ┌──────────────┐         ┌───────────────────┐                 │   │
│   │  │   Notify     │────────►│  SNS (analysts)   │                 │   │
│   │  │  (summary)   │         └───────────────────┘                 │   │
│   │  └──────────────┘                                               │   │
│   │                                                                 │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scheduler | EventBridge | Native AWS, serverless, simple cron |
| Orchestration | Step Functions | Fan-out parallelism, built-in retry, single notification after all complete |
| Compute | Lambda (swappable to Fargate) | Lambda for < 15 min tasks; Fargate for longer/cheaper |
| Notifications | SNS | Multi-channel, decoupled |
| Error Handling | Retry + Catch | Automatic retry with backoff, route failures to notify |

### Trade-offs

- **Lambda vs Fargate:** Lambda is simpler but 15-min limit. Fargate is cheaper for sustained compute but more setup.
- **Step Functions billing:** Standard workflows charge per transition, not duration — waiting is free.

---

## Challenge 4: NFL Scoreboard App

**Objective:** Static frontend displaying live scores and standings from a serverless API.

### Architecture
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Frontend                                                           │   │
│   │  S3 Static Website                                                  │   │
│   │  • index.html (polls API every 30s)                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              │ HTTP                                         │
│                              ▼                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  API Gateway (REST API)                                             │   │
│   │                                                                     │   │
│   │  GET /scores ─────► Lambda ─────► DynamoDB (nfl-scores)             │   │
│   │                                                                     │   │
│   │  GET /standings ──► Lambda ─────► DynamoDB (nfl-standings)          │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend | S3 static website | Simple, cheap, scales infinitely |
| API | REST API | LocalStack free tier compatible; HTTP API would be cheaper in prod |
| Database | DynamoDB (PAY_PER_REQUEST) | Key-value lookups, auto-scaling, no capacity planning |
| Compute | Separate Lambdas per endpoint | Single responsibility, independent scaling |
| Real-time | Polling (30s) | Simple; maybe WebSocket API for true real-time |

### Trade-offs

- **Polling vs WebSocket:** Polling is simpler but not truly real-time. For live game updates, WebSocket API with DynamoDB Streams would push instantly.
- **REST vs HTTP API:** Had to use REST API with free version of LocalStack. Generally, REST API is more verbose but has caching, usage plans. HTTP API is cheaper/faster but fewer features. I would have used HTTP in this case.
- **CloudFront:** Not included for simplicity. In prod, add for HTTPS + CDN caching.

---

## Best Practices Demonstrated

| Practice | Where |
|----------|-------|
| `default_tags` in provider | All challenges — Environment, ManagedBy |
| File organization | Separate files per service (s3.tf, iam.tf, lambda.tf) |
| Least privilege IAM | Scoped to specific resources |
| `data` blocks for policies | `aws_iam_policy_document` over inline JSON for challenge 3+4 |

---
