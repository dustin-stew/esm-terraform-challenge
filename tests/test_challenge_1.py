"""
Challenge 1: S3 Bucket
Verifies that an S3 bucket named "ncaa" exists.
"""


class TestS3Bucket:

    def test_ncaa_bucket_exists(self, aws_clients):
        """S3 bucket named 'ncaa' must exist."""
        resp = aws_clients["s3"].list_buckets()
        bucket_names = [b["Name"] for b in resp["Buckets"]]
        assert "ncaa" in bucket_names, (
            f"Bucket 'ncaa' not found. Existing buckets: {bucket_names}"
        )
