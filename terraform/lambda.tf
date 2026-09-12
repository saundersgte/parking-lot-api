resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/parking-lot-api"
  retention_in_days = 14

  tags = {
    Project = "parking-lot-api"
  }
}