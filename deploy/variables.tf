variable "artifact_bucket" {
  description = "S3 bucket where build artifacts are uploaded to"
}

variable "artifact_name" {
  description = "Key to artifact uploaded to S3"
}

variable "iam_role" {
  description = "IAM role assumed by the lambda"
}
