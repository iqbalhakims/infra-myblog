resource aws_s3_bucket "iqbalhakim" {
    bucket = "var.bucket_name"
}

resource "aws_s3_bucket_public_access_block" "block" {
  bucket = aws_s3_bucket.iqbalhakim.id

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

resource "aws_s3_bucket" "object" {
  
  for_each = fileset("${path.module/www}","**/*")
  bucket = aws_s3_bucket.my_blog.id
  key    = each.value 
  source = "${path.module/www}/${each.value}"
  etag = filemd5("${path.module/www}/${each.value}")
  content_type = lookup({
    "html" = "text/html",
    "css"  = "text/css",
    "js"   = "application/javascript",
    "png"  = "image/png",
    "jpg"  = "image/jpeg",
    "jpeg" = "image/jpeg",
    "gif"  = "image/gif",
    "svg"  = "image/svg+xml",
    "json" = "application/json",
    "xml"  = "application/xml"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "application/octet-stream")
}


resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name              = aws_s3_bucket.iqbalhakim.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
    origin_id                = local.origin_id
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Some comment"
  default_root_object = "index.html"

  logging_config {
    include_cookies = false
    bucket          = "mylogs.s3.amazonaws.com"
    prefix          = "myprefix"
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = local.origin_id

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}