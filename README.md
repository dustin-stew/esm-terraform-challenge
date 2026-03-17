## **${\textsf{\color{green}My solution README can be found }}$[here](interview_questions/README.md).**
## 
# Terraform Interview Challenge

A hands-on Terraform coding challenge that runs entirely on your local machine using [LocalStack](https://localstack.cloud/) to emulate AWS services. No AWS account required.

## Use of AI is permitted, be prepared to discuss your approach and reasoning.

This challenge was designed in a MacOS environment, some commands may differ depending on your OS.

## Prerequisites

Make sure the following are installed before starting:

| Tool | Version | Install |
|------|---------|---------|
| **Docker** | 20.10+ | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| **Docker Compose** | v2+ | Included with Docker Desktop |
| **Terraform** | >= 1.0 | [developer.hashicorp.com/terraform/install](https://developer.hashicorp.com/terraform/install) |
| **Python** | 3.9+ | [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | latest | Included with Python |
| **Local Stack** | latest | [localstak installation](https://docs.localstack.cloud/aws/getting-started/installation/) |

Verify your installations:

```bash
docker --version
docker compose version
terraform --version
python3 --version
localstack --version
```

## Project Structure

```
interview-challenge/
├── docker-compose.yml                        # LocalStack container setup
├── interview_questions/
│   ├── terraform_challenge_code/
│   │   ├── main.tf                           # Provider config (DO NOT MODIFY)
│   │   └── s3.tf                             # Candidate works here
│   └── app/                                  # Supporting files for challenges
└── tests/
    ├── conftest.py                           # Pytest fixtures / boto3 client setup
    ├── requirements.txt                      # Python test dependencies
    └── test_challenge_1.py                   # Automated validation tests
```

## Setup

### 1. Start LocalStack

From the `interview-questions/` directory:

```bash
cd interview-questions
docker compose up -d
```

Wait for LocalStack to be healthy:

```bash
docker compose ps
```

You should see `localstack` with status `healthy`. You can also verify manually:

```bash
curl http://localhost:4566/_localstack/health
```

### 2. Install Python Test Dependencies

```bash
pip install -r tests/requirements.txt
```

### 3. Initialize Terraform

```bash
cd interview_questions/$(challenge_folder)
terraform init
```

## Completing the Challenge

1. Open the `.tf` files in `interview_questions/`
2. Read the `requirements.md` in each folder and implement the required resources
3. **Do not modify `main.tf`** — it is pre-configured to point to LocalStack

### Apply Your Changes

From inside `interview_questions/`:

```bash
terraform plan      # Preview what will be created
terraform apply     # Apply changes (type "yes" when prompted)
```

Or skip the confirmation prompt:

```bash
terraform apply -auto-approve
```

## Running the Tests

```bash
# Run all tests
pytest tests/

# Run Non verbose short version
pytest -q --tb=short

# Run a specific challenge's tests
pytest tests/test_challenge_1.py

# Run with verbose output
pytest tests/test_challenge_1.py -v
```

A passing test looks like:

```
tests/test_challenge_1.py::TestS3Bucket::test_ncaa_bucket_exists PASSED
```

## Quick Reference — Full Workflow

```bash
# 1. Start LocalStack
cd interview-challenge
docker compose up -d

# 2. Install test dependencies
pip install -r tests/requirements.txt

# 3. Initialize and apply Terraform
cd interview_questions/
terraform init
terraform apply -auto-approve

# 4. Run tests (from interview-challenge/ directory)
cd ../..
pytest tests/ -v
```

## Troubleshooting

**LocalStack not starting:**
```bash
docker compose down
docker compose up -d
```

**Terraform state is stale or corrupted:**
```bash
cd interview_questions/terraform_challenge_code
terraform destroy -auto-approve
terraform apply -auto-approve
```

**Tests can't connect to LocalStack:**
- Make sure the container is running: `docker compose ps`
- Make sure port 4566 is not in use by another process
- Check LocalStack logs: `docker compose logs localstack`

**Starting fresh (reset everything):**
```bash
docker compose down -v
docker compose up -d
cd interview_questions/terraform_challenge_code
rm -f terraform.tfstate terraform.tfstate.backup
terraform init
```
