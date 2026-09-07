resource "aws_dynamodb_table" "parking_spots" {
  name         = "parking_spots"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "spot_id"

  attribute {
    name = "spot_id"
    type = "S"
  }

  tags = {
    Project = "parking-lot-api"
  }
}