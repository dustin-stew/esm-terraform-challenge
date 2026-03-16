# ------------------------------------------------------------------------------
# S3 Bucket - Data Storage
# ------------------------------------------------------------------------------

resource "aws_s3_bucket" "data_pipeline" {
  bucket        = "sports-data-pipeline"
  force_destroy = true
}