# Challenge 5: Scheduled Data Pipeline with Notifications

### Use of AI
Use of AI is permitted so long as its used as a tool and the candidate is able to explain their decisions.

## Scenario

A sports analytics company needs a pipeline that runs on a schedule, processes game data files, and notifies analysts when results are ready or when errors occur.

## Requirements

- A job runs on a recurring schedule (e.g., every hour)
- The job picks up raw data files from a storage location, processes them, and writes the results to a separate location
- Notifies successfull processing
- Handle failures in a graceful manner

## Deliverables

### Provide Terraform code that creates all the infrastructure needed to meet the requirements.

> The Terraform code should pass `terraform plan` and `terraform apply` without errors.

### Provide a high-level architecture description including:
- Which services you chose and why
- How these services interact
- Be prepared to discuss trade-offs in your design decisions