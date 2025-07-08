resource "aws_s3_bucket" "site" {
  bucket = "${var.project_name}-site"
}

resource "aws_s3_bucket_website_configuration" "site" {
  bucket = aws_s3_bucket.site.id
  index_document {
    suffix = "index.html"
  }
}
