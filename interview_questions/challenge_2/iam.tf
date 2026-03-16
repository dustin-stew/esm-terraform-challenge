# ------------------------------------------------------------------------------
# Part A: Read-Only User
# ------------------------------------------------------------------------------

# user
resource "aws_iam_user" "ncaa_analyst" {
  name = "ncaa-analyst"
}

# user policy
resource "aws_iam_policy" "ncaa_s3_read_only" {
  name        = "ncaa-s3-read-only"
  description = "Read-only access to NCAA S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "AllowGetObject"
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.ncaa.arn}/*"
      },
      {
        Sid      = "AllowListBucket"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.ncaa.arn
      }
    ]
  })
}
# attachment
resource "aws_iam_user_policy_attachment" "ncaa_analyst_read_only" {
  user       = aws_iam_user.ncaa_analyst.name
  policy_arn = aws_iam_policy.ncaa_s3_read_only.arn
}

# ------------------------------------------------------------------------------
# Part B: Read + Write Role
# ------------------------------------------------------------------------------

# role
resource "aws_iam_role" "ncaa_data_writer" {
  name = "ncaa-data-writer"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# role policy
resource "aws_iam_policy" "ncaa_s3_read_write" {
  name        = "ncaa-s3-read-write"
  description = "Read/write access to NCAA S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowObjectOperations"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.ncaa.arn}/*"
      },
      {
        Sid      = "AllowListBucket"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.ncaa.arn
      }
    ]
  })
}

# role policy attachment
resource "aws_iam_role_policy_attachment" "ncaa_data_writer_read_write" {
  role       = aws_iam_role.ncaa_data_writer.name
  policy_arn = aws_iam_policy.ncaa_s3_read_write.arn
}