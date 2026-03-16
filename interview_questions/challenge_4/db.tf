# ------------------------------------------------------------------------------
# DynamoDB - Game Scores
# ------------------------------------------------------------------------------

resource "aws_dynamodb_table" "scores" {
  name         = "nfl-scores"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "gameId"

  attribute {
    name = "gameId"
    type = "S"
  }
}

# ------------------------------------------------------------------------------
# DynamoDB - Team Standings
# ------------------------------------------------------------------------------

resource "aws_dynamodb_table" "standings" {
  name         = "nfl-standings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "teamId"

  attribute {
    name = "teamId"
    type = "S"
  }
}