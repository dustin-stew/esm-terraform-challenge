import pytest
import boto3

LOCALSTACK_ENDPOINT = "http://localhost:4566"


@pytest.fixture(scope="session")
def aws_clients():
    """Boto3 clients pointed at LocalStack."""
    session = boto3.Session(
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )
    return {
        "s3": session.client("s3", endpoint_url=LOCALSTACK_ENDPOINT),
        "dynamodb": session.client("dynamodb", endpoint_url=LOCALSTACK_ENDPOINT),
        "ssm": session.client("ssm", endpoint_url=LOCALSTACK_ENDPOINT),
        "lambda": session.client("lambda", endpoint_url=LOCALSTACK_ENDPOINT),
        "iam": session.client("iam", endpoint_url=LOCALSTACK_ENDPOINT),
        "logs": session.client("logs", endpoint_url=LOCALSTACK_ENDPOINT),
        "sqs": session.client("sqs", endpoint_url=LOCALSTACK_ENDPOINT),
        "stepfunctions": session.client("stepfunctions", endpoint_url=LOCALSTACK_ENDPOINT),
        "sns": session.client("sns", endpoint_url=LOCALSTACK_ENDPOINT),
        "apigateway": session.client("apigateway", endpoint_url=LOCALSTACK_ENDPOINT),
    }
