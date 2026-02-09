resource aws_s3_bucket " my_blog" {
    bucket = "var.bucket_name"
    

}

resource "aws_s3_bucket_public_access_block" "block" {
  bucket = aws_s3_bucket.my_blog.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
} 