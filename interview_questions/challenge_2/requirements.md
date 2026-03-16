
# Challenge 2: IAM — S3 Access Control

The "ncaa" S3 bucket needs access controls. Create an IAM user with
read-only access and a separate IAM role for a service that needs
read/write access. Then apply a bucket policy.

# Part A — Read-Only User
Create an IAM user named "ncaa-analyst"

Create an IAM policy named "ncaa-s3-read-only" that grants:
   - s3:GetObject on "arn:aws:s3:::ncaa/*"
  - s3:ListBucket on "arn:aws:s3:::ncaa"

TODO: Attach the policy to the user

# Part B — Read/Write Role
TODO: Create an IAM role named "ncaa-data-writer" with a trust policy
       that allows the "ec2.amazonaws.com" service to assume it

TODO: Create an IAM policy named "ncaa-s3-read-write" that grants:
   - s3:GetObject on "arn:aws:s3:::ncaa/*"
   - s3:PutObject on "arn:aws:s3:::ncaa/*"
   - s3:DeleteObject on "arn:aws:s3:::ncaa/*"
   - s3:ListBucket on "arn:aws:s3:::ncaa"

TODO: Attach the policy to the role

# Part C — Bucket Policy (Enforce Encryption)
 TODO: Create an S3 bucket policy on the "ncaa" bucket that denies
       s3:PutObject when the request does NOT include
       "s3:x-amz-server-side-encryption" = "AES256"