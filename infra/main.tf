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

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "demo-oac"
  description                       = "Example Policy"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}


