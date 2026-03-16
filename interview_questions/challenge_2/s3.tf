# ------------------------------------------------------------------------------
# S3 Bucket
# ------------------------------------------------------------------------------

resource "aws_s3_bucket" "ncaa" {
  bucket        = "ncaa"
  force_destroy = true
}

# ------------------------------------------------------------------------------
# Bucket Policy - Deny unencrypted uploads
# ------------------------------------------------------------------------------

resource "aws_s3_bucket_policy" "ncaa_enforce_encryption" {
  bucket = aws_s3_bucket.ncaa.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyUnencryptedUploads"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.ncaa.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      },
      {
        Sid       = "DenyNoEncryptionHeader"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.ncaa.arn}/*"
        Condition = {
            Null = {
            "s3:x-amz-server-side-encryption" = "true"
            }
        }
    }
    ]
  })
}