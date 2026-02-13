resource aws_s3_bucket "my_blog" {
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

resource "aws_s3_bucket_policy" "allow_cloudfront" {
  depends_on = [aws_s3_bucket_public_access_block.block]
  bucket = aws_s3_bucket.my_blog.id
  
policy = jsonencode({
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFront",
      "Effect": "Allow",
      "Principal": {
        "AWS": "cloudfront.amazonaws.com"
      },
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": "${aws_s3_bucket.my_blog.arn}/*"
    }
  ]
})
}

data "aws_iam_policy_document" "allow_access_from_another_account" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["123456789012"]
    }

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.example.arn,
      "${aws_s3_bucket.example.arn}/*",
    ]
  }
}

resource "aws_s3_bucket_object" "object" {
  
  for_each = fileset("${path.module/www}","**/*")
  bucket = aws_s3_bucket.my_blog.id
  key    = each.value 
  source = "${path.module/www}/${each.value}"
  etag = filemd5("${path.module/www}/${each.value}")
}
