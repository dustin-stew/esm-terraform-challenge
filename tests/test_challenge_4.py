"""
Challenge 4: NFL Scoreboard App
Verifies infrastructure (S3, DynamoDB, API Gateway, Lambda) and API responses.
"""
import json

import boto3

LOCALSTACK_ENDPOINT = "http://localhost:4566"

SCORES_TABLE = "nfl-scores"
STANDINGS_TABLE = "nfl-standings"
FRONTEND_BUCKET = "nfl-scoreboard-frontend"

SEED_SCORES = [
    {"gameId": "game-001", "homeTeam": "Chiefs", "awayTeam": "Ravens", "homeScore": 27, "awayScore": 24, "status": "Final"},
    {"gameId": "game-002", "homeTeam": "Cowboys", "awayTeam": "Eagles", "homeScore": 14, "awayScore": 21, "status": "Q4 2:30"},
]

SEED_STANDINGS = [
    {"teamId": "Chiefs", "wins": 11, "losses": 1, "conference": "AFC"},
    {"teamId": "Ravens", "wins": 10, "losses": 2, "conference": "AFC"},
]


def _get_rest_api_id(aws_clients):
    resp = aws_clients["apigateway"].get_rest_apis()
    for api in resp["items"]:
        if api["name"] == "nfl-scoreboard-api":
            return api["id"]
    raise AssertionError("REST API 'nfl-scoreboard-api' not found")


def _seed_tables(aws_clients):
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    scores = dynamodb.Table(SCORES_TABLE)
    for item in SEED_SCORES:
        scores.put_item(Item=item)

    standings = dynamodb.Table(STANDINGS_TABLE)
    for item in SEED_STANDINGS:
        standings.put_item(Item=item)


class TestScoreboardInfrastructure:
    """Verify all Challenge 4 resources exist."""

    def test_frontend_bucket_exists(self, aws_clients):
        resp = aws_clients["s3"].list_buckets()
        names = [b["Name"] for b in resp["Buckets"]]
        assert FRONTEND_BUCKET in names, f"Bucket '{FRONTEND_BUCKET}' not found. Existing: {names}"

    def test_frontend_has_index_html(self, aws_clients):
        resp = aws_clients["s3"].get_object(Bucket=FRONTEND_BUCKET, Key="index.html")
        body = resp["Body"].read().decode("utf-8")
        assert "NFL Scoreboard" in body, "index.html missing or doesn't contain expected content"

    def test_frontend_index_has_api_url(self, aws_clients):
        """index.html should have the API URL injected (not the placeholder)."""
        resp = aws_clients["s3"].get_object(Bucket=FRONTEND_BUCKET, Key="index.html")
        body = resp["Body"].read().decode("utf-8")
        assert "__API_URL__" not in body, "API_URL placeholder was not replaced by Terraform"
        assert "/restapis/" in body, "index.html does not contain a valid API Gateway URL"

    def test_scores_table_exists(self, aws_clients):
        resp = aws_clients["dynamodb"].describe_table(TableName=SCORES_TABLE)
        assert resp["Table"]["TableName"] == SCORES_TABLE

    def test_standings_table_exists(self, aws_clients):
        resp = aws_clients["dynamodb"].describe_table(TableName=STANDINGS_TABLE)
        assert resp["Table"]["TableName"] == STANDINGS_TABLE

    def test_scores_table_has_streams(self, aws_clients):
        resp = aws_clients["dynamodb"].describe_table(TableName=SCORES_TABLE)
        stream_spec = resp["Table"].get("StreamSpecification", {})
        assert stream_spec.get("StreamEnabled") is True, "DynamoDB Streams not enabled on scores table"

    def test_standings_table_has_streams(self, aws_clients):
        resp = aws_clients["dynamodb"].describe_table(TableName=STANDINGS_TABLE)
        stream_spec = resp["Table"].get("StreamSpecification", {})
        assert stream_spec.get("StreamEnabled") is True, "DynamoDB Streams not enabled on standings table"

    def test_lambda_functions_exist(self, aws_clients):
        resp = aws_clients["lambda"].list_functions()
        names = [f["FunctionName"] for f in resp["Functions"]]
        for fn in ["get-scores", "get-standings"]:
            assert fn in names, f"Lambda '{fn}' not found. Existing: {names}"

    def test_rest_api_exists(self, aws_clients):
        resp = aws_clients["apigateway"].get_rest_apis()
        names = [api["name"] for api in resp["items"]]
        assert "nfl-scoreboard-api" in names, f"REST API not found. Existing: {names}"


class TestScoreboardAPI:
    """Test the actual API endpoints return valid data."""

    def test_scores_endpoint(self, aws_clients):
        _seed_tables(aws_clients)
        api_id = _get_rest_api_id(aws_clients)

        import urllib.request
        url = f"http://localhost:4566/restapis/{api_id}/prod/_user_request_/scores"
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read().decode("utf-8"))

        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) >= 2, f"Expected at least 2 scores, got {len(data)}"

        game_ids = [g["gameId"] for g in data]
        assert "game-001" in game_ids, f"game-001 not found in response: {game_ids}"
        print(f"  PASS: /scores returned {len(data)} games")

    def test_standings_endpoint(self, aws_clients):
        _seed_tables(aws_clients)
        api_id = _get_rest_api_id(aws_clients)

        import urllib.request
        url = f"http://localhost:4566/restapis/{api_id}/prod/_user_request_/standings"
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read().decode("utf-8"))

        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) >= 2, f"Expected at least 2 standings, got {len(data)}"

        team_ids = [t["teamId"] for t in data]
        assert "Chiefs" in team_ids, f"Chiefs not found in response: {team_ids}"
        print(f"  PASS: /standings returned {len(data)} teams")

    def test_scores_response_format(self, aws_clients):
        """Verify score objects have expected fields."""
        _seed_tables(aws_clients)
        api_id = _get_rest_api_id(aws_clients)

        import urllib.request
        url = f"http://localhost:4566/restapis/{api_id}/prod/_user_request_/scores"
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read().decode("utf-8"))

        game = next(g for g in data if g["gameId"] == "game-001")
        for field in ["gameId", "homeTeam", "awayTeam", "homeScore", "awayScore", "status"]:
            assert field in game, f"Missing field '{field}' in score response"

    def test_standings_response_format(self, aws_clients):
        """Verify standings objects have expected fields."""
        _seed_tables(aws_clients)
        api_id = _get_rest_api_id(aws_clients)

        import urllib.request
        url = f"http://localhost:4566/restapis/{api_id}/prod/_user_request_/standings"
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read().decode("utf-8"))

        team = next(t for t in data if t["teamId"] == "Chiefs")
        for field in ["teamId", "wins", "losses"]:
            assert field in team, f"Missing field '{field}' in standings response"