data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../build"
  output_path = "${path.module}/../build.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/parking-lot-api"
  retention_in_days = 14

  tags = {
    Project = "parking-lot-api"
  }
}

resource "aws_lambda_function" "api" {
  function_name = "parking-lot-api"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "app.main.handler"
  runtime       = "python3.13"

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  timeout     = 10
  memory_size = 512

  environment {
    variables = {
      SPOTS_TABLE = aws_dynamodb_table.parking_spots.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]

  tags = {
    Project = "parking-lot-api"
  }
}