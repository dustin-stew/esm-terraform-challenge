# ------------------------------------------------------------------------------
# S3 Bucket - NCAA Data Blob Storage
# ------------------------------------------------------------------------------

resource "aws_s3_bucket" "ncaa" {
  bucket        = "ncaa"
  force_destroy = true

  tags = {
    Project     = "ncaa"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}