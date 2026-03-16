"""
Challenge 2: IAM — S3 Access Control
Verifies IAM user, role, policies, and S3 bucket policy.
"""

import json


class TestIAMReadOnlyUser:
    """Part A — Read-Only User"""

    def test_ncaa_analyst_user_exists(self, aws_clients):
        """IAM user 'ncaa-analyst' must exist."""
        resp = aws_clients["iam"].get_user(UserName="ncaa-analyst")
        assert resp["User"]["UserName"] == "ncaa-analyst"

    def test_read_only_policy_exists(self, aws_clients):
        """IAM policy 'ncaa-s3-read-only' must exist."""
        resp = aws_clients["iam"].list_policies(Scope="Local")
        policy_names = [p["PolicyName"] for p in resp["Policies"]]
        assert "ncaa-s3-read-only" in policy_names, (
            f"Policy 'ncaa-s3-read-only' not found. Existing policies: {policy_names}"
        )

    def test_read_only_policy_actions(self, aws_clients):
        """Read-only policy must only grant s3:GetObject and s3:ListBucket."""
        policy_arn = _get_policy_arn(aws_clients["iam"], "ncaa-s3-read-only")
        doc = _get_policy_document(aws_clients["iam"], policy_arn)

        all_actions = set()
        for stmt in doc["Statement"]:
            actions = stmt["Action"]
            if isinstance(actions, str):
                actions = [actions]
            all_actions.update(actions)

        assert all_actions == {"s3:GetObject", "s3:ListBucket"}, (
            f"Expected only s3:GetObject and s3:ListBucket, got: {all_actions}"
        )

    def test_read_only_policy_no_write_actions(self, aws_clients):
        """Read-only policy must NOT include any write actions."""
        policy_arn = _get_policy_arn(aws_clients["iam"], "ncaa-s3-read-only")
        doc = _get_policy_document(aws_clients["iam"], policy_arn)

        write_actions = {"s3:PutObject", "s3:DeleteObject", "s3:PutBucketPolicy"}
        for stmt in doc["Statement"]:
            actions = stmt["Action"]
            if isinstance(actions, str):
                actions = [actions]
            for action in actions:
                assert action not in write_actions, (
                    f"Read-only policy should not contain write action: {action}"
                )

    def test_read_only_policy_scoped_to_ncaa_bucket(self, aws_clients):
        """Read-only policy resources must be scoped to the ncaa bucket."""
        policy_arn = _get_policy_arn(aws_clients["iam"], "ncaa-s3-read-only")
        doc = _get_policy_document(aws_clients["iam"], policy_arn)

        all_resources = set()
        for stmt in doc["Statement"]:
            resources = stmt["Resource"]
            if isinstance(resources, str):
                resources = [resources]
            all_resources.update(resources)

        for resource in all_resources:
            assert "ncaa" in resource, (
                f"Resource '{resource}' is not scoped to the ncaa bucket"
            )

    def test_read_only_policy_attached_to_user(self, aws_clients):
        """Read-only policy must be attached to the ncaa-analyst user."""
        resp = aws_clients["iam"].list_attached_user_policies(
            UserName="ncaa-analyst"
        )
        attached_names = [p["PolicyName"] for p in resp["AttachedPolicies"]]
        assert "ncaa-s3-read-only" in attached_names, (
            f"Policy not attached to user. Attached policies: {attached_names}"
        )


class TestIAMReadWriteRole:
    """Part B — Read/Write Role"""

    def test_data_writer_role_exists(self, aws_clients):
        """IAM role 'ncaa-data-writer' must exist."""
        resp = aws_clients["iam"].get_role(RoleName="ncaa-data-writer")
        assert resp["Role"]["RoleName"] == "ncaa-data-writer"

    def test_data_writer_trust_policy(self, aws_clients):
        """Role trust policy must allow ec2.amazonaws.com to assume it."""
        resp = aws_clients["iam"].get_role(RoleName="ncaa-data-writer")
        trust = resp["Role"]["AssumeRolePolicyDocument"]

        if isinstance(trust, str):
            trust = json.loads(trust)

        services = []
        for stmt in trust["Statement"]:
            principal = stmt.get("Principal", {})
            service = principal.get("Service", "")
            if isinstance(service, str):
                services.append(service)
            else:
                services.extend(service)

        assert "ec2.amazonaws.com" in services, (
            f"Trust policy does not allow ec2.amazonaws.com. Found: {services}"
        )

    def test_read_write_policy_exists(self, aws_clients):
        """IAM policy 'ncaa-s3-read-write' must exist."""
        resp = aws_clients["iam"].list_policies(Scope="Local")
        policy_names = [p["PolicyName"] for p in resp["Policies"]]
        assert "ncaa-s3-read-write" in policy_names, (
            f"Policy 'ncaa-s3-read-write' not found. Existing policies: {policy_names}"
        )

    def test_read_write_policy_actions(self, aws_clients):
        """Read-write policy must grant all four required actions."""
        policy_arn = _get_policy_arn(aws_clients["iam"], "ncaa-s3-read-write")
        doc = _get_policy_document(aws_clients["iam"], policy_arn)

        all_actions = set()
        for stmt in doc["Statement"]:
            actions = stmt["Action"]
            if isinstance(actions, str):
                actions = [actions]
            all_actions.update(actions)

        expected = {"s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"}
        assert expected.issubset(all_actions), (
            f"Missing actions. Expected {expected}, got: {all_actions}"
        )

    def test_read_write_policy_scoped_to_ncaa_bucket(self, aws_clients):
        """Read-write policy resources must be scoped to the ncaa bucket."""
        policy_arn = _get_policy_arn(aws_clients["iam"], "ncaa-s3-read-write")
        doc = _get_policy_document(aws_clients["iam"], policy_arn)

        all_resources = set()
        for stmt in doc["Statement"]:
            resources = stmt["Resource"]
            if isinstance(resources, str):
                resources = [resources]
            all_resources.update(resources)

        for resource in all_resources:
            assert "ncaa" in resource, (
                f"Resource '{resource}' is not scoped to the ncaa bucket"
            )

    def test_read_write_policy_attached_to_role(self, aws_clients):
        """Read-write policy must be attached to the ncaa-data-writer role."""
        resp = aws_clients["iam"].list_attached_role_policies(
            RoleName="ncaa-data-writer"
        )
        attached_names = [p["PolicyName"] for p in resp["AttachedPolicies"]]
        assert "ncaa-s3-read-write" in attached_names, (
            f"Policy not attached to role. Attached policies: {attached_names}"
        )


class TestS3BucketPolicy:
    """Part C — Bucket Policy (Enforce Encryption)"""

    def test_bucket_policy_exists(self, aws_clients):
        """The ncaa bucket must have a bucket policy."""
        resp = aws_clients["s3"].get_bucket_policy(Bucket="ncaa")
        policy = json.loads(resp["Policy"])
        assert "Statement" in policy, "Bucket policy has no Statement"

    def test_bucket_policy_denies_unencrypted_uploads(self, aws_clients):
        """Bucket policy must deny PutObject without AES256 encryption."""
        resp = aws_clients["s3"].get_bucket_policy(Bucket="ncaa")
        policy = json.loads(resp["Policy"])

        deny_stmts = [s for s in policy["Statement"] if s["Effect"] == "Deny"]
        assert len(deny_stmts) > 0, "No Deny statements found in bucket policy"

        found_encryption_deny = False
        for stmt in deny_stmts:
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            condition = stmt.get("Condition", {})
            string_not_equals = condition.get("StringNotEquals", {})

            if "s3:PutObject" in actions and \
               "s3:x-amz-server-side-encryption" in string_not_equals:
                assert string_not_equals["s3:x-amz-server-side-encryption"] == "AES256"
                found_encryption_deny = True

        assert found_encryption_deny, (
            "No Deny statement found that blocks unencrypted PutObject uploads. "
            "Expected a Deny with Condition StringNotEquals "
            "s3:x-amz-server-side-encryption = AES256"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_policy_arn(iam_client, policy_name):
    """Look up a customer-managed policy ARN by name."""
    resp = iam_client.list_policies(Scope="Local")
    for p in resp["Policies"]:
        if p["PolicyName"] == policy_name:
            return p["Arn"]
    raise AssertionError(f"Policy '{policy_name}' not found")


def _get_policy_document(iam_client, policy_arn):
    """Fetch and parse the default version of a policy."""
    meta = iam_client.get_policy(PolicyArn=policy_arn)
    version_id = meta["Policy"]["DefaultVersionId"]
    version = iam_client.get_policy_version(
        PolicyArn=policy_arn, VersionId=version_id
    )
    doc = version["PolicyVersion"]["Document"]
    if isinstance(doc, str):
        doc = json.loads(doc)
    return doc
