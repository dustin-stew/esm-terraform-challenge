"""
Challenge 3: Event-Driven Data Pipeline
End-to-end test: S3 upload → SQS → Step Functions → SNS notification
"""
import json
import time

BUCKET = "sports-data-pipeline"
QUEUE_NAME = "sports-data-file-events"
STATE_MACHINE_NAME = "sports-data-pipeline"
SNS_TOPIC_NAME = "pipeline-notifications"


class TestPipelineInfrastructure:
    """Verify all pipeline resources exist."""

    def test_s3_bucket_exists(self, aws_clients):
        resp = aws_clients["s3"].list_buckets()
        names = [b["Name"] for b in resp["Buckets"]]
        assert BUCKET in names, f"Bucket '{BUCKET}' not found. Existing: {names}"

    def test_sqs_queue_exists(self, aws_clients):
        resp = aws_clients["sqs"].list_queues()
        urls = resp.get("QueueUrls", [])
        assert any(QUEUE_NAME in url for url in urls), (
            f"Queue '{QUEUE_NAME}' not found. Existing: {urls}"
        )

    def test_state_machine_exists(self, aws_clients):
        resp = aws_clients["stepfunctions"].list_state_machines()
        names = [sm["name"] for sm in resp["stateMachines"]]
        assert STATE_MACHINE_NAME in names, (
            f"State machine '{STATE_MACHINE_NAME}' not found. Existing: {names}"
        )

    def test_sns_topic_exists(self, aws_clients):
        resp = aws_clients["sns"].list_topics()
        arns = [t["TopicArn"] for t in resp["Topics"]]
        assert any(SNS_TOPIC_NAME in arn for arn in arns), (
            f"SNS topic '{SNS_TOPIC_NAME}' not found. Existing: {arns}"
        )

    def test_lambda_functions_exist(self, aws_clients):
        resp = aws_clients["lambda"].list_functions()
        names = [f["FunctionName"] for f in resp["Functions"]]
        for fn in ["drain-queue", "process-file", "notify"]:
            assert fn in names, f"Lambda '{fn}' not found. Existing: {names}"

    def test_eventbridge_schedule_exists(self, aws_clients):
        events = aws_clients["logs"]  # reuse session
        session = events._endpoint._endpoint_prefix  # noqa
        # Use a direct events client
        import boto3
        events_client = boto3.client(
            "events",
            endpoint_url="http://localhost:4566",
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        resp = events_client.list_rules()
        names = [r["Name"] for r in resp["Rules"]]
        assert "pipeline-schedule" in names, (
            f"EventBridge rule 'pipeline-schedule' not found. Existing: {names}"
        )


class TestPipelineEndToEnd:
    """End-to-end pipeline test: upload files → trigger pipeline → verify."""

    def _get_queue_url(self, aws_clients):
        resp = aws_clients["sqs"].list_queues(QueueNamePrefix=QUEUE_NAME)
        return resp["QueueUrls"][0]

    def _get_state_machine_arn(self, aws_clients):
        resp = aws_clients["stepfunctions"].list_state_machines()
        for sm in resp["stateMachines"]:
            if sm["name"] == STATE_MACHINE_NAME:
                return sm["stateMachineArn"]
        raise AssertionError(f"State machine '{STATE_MACHINE_NAME}' not found")

    def test_s3_upload_triggers_sqs_message(self, aws_clients):
        """Uploading a file to S3 raw/ should produce an SQS message."""
        s3 = aws_clients["s3"]
        sqs = aws_clients["sqs"]
        queue_url = self._get_queue_url(aws_clients)

        # Drain any existing messages
        while True:
            resp = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=1)
            if not resp.get("Messages"):
                break
            for msg in resp["Messages"]:
                sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg["ReceiptHandle"])

        # Upload test files
        test_files = [
            ("raw/game_test_001.json", {"gameId": "test-001", "homeTeam": "TestA", "awayTeam": "TestB", "score": "24-17"}),
            ("raw/game_test_002.json", {"gameId": "test-002", "homeTeam": "TestC", "awayTeam": "TestD", "score": "10-7"}),
        ]
        for key, data in test_files:
            s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(data))
            print(f"  Uploaded s3://{BUCKET}/{key}")

        # Wait for SQS to receive the S3 notifications
        time.sleep(3)

        # Check messages arrived
        resp = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=["ApproximateNumberOfMessages"]
        )
        msg_count = int(resp["Attributes"]["ApproximateNumberOfMessages"])
        print(f"  SQS messages available: {msg_count}")
        assert msg_count >= 2, f"Expected at least 2 SQS messages, got {msg_count}"

    def test_step_functions_execution(self, aws_clients):
        """Manually trigger Step Functions and verify it completes successfully."""
        sfn = aws_clients["stepfunctions"]
        sm_arn = self._get_state_machine_arn(aws_clients)

        # Start execution
        resp = sfn.start_execution(stateMachineArn=sm_arn)
        execution_arn = resp["executionArn"]
        print(f"  Started execution: {execution_arn}")

        # Poll for completion (max 60 seconds)
        for i in range(30):
            resp = sfn.describe_execution(executionArn=execution_arn)
            status = resp["status"]
            print(f"  Execution status: {status} ({i + 1}s)")

            if status in ("SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"):
                break
            time.sleep(2)

        if status == "SUCCEEDED":
            output = json.loads(resp.get("output", "{}"))
            print(f"  Output: {json.dumps(output, indent=2)}")

        assert status == "SUCCEEDED", (
            f"Execution {status}. Expected SUCCEEDED. "
            f"Error: {resp.get('error', 'N/A')} - {resp.get('cause', 'N/A')}"
        )

    def test_processed_files_cleanup(self, aws_clients):
        """Clean up test files after pipeline run."""
        s3 = aws_clients["s3"]
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix="raw/game_test_")
        for obj in resp.get("Contents", []):
            s3.delete_object(Bucket=BUCKET, Key=obj["Key"])
            print(f"  Cleaned up: {obj['Key']}")