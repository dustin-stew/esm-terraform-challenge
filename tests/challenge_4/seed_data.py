import boto3

# LocalStack endpoint
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

# Seed scores
scores_table = dynamodb.Table('nfl-scores')
scores = [
    {'gameId': 'game-001', 'homeTeam': 'Chiefs', 'awayTeam': 'Ravens', 'homeScore': 27, 'awayScore': 24, 'status': 'Final'},
    {'gameId': 'game-002', 'homeTeam': 'Cowboys', 'awayTeam': 'Eagles', 'homeScore': 14, 'awayScore': 21, 'status': 'Q4 2:30'},
    {'gameId': 'game-003', 'homeTeam': '49ers', 'awayTeam': 'Rams', 'homeScore': 0, 'awayScore': 0, 'status': 'Upcoming'},
]

for score in scores:
    scores_table.put_item(Item=score)
    print(f"Added: {score['homeTeam']} vs {score['awayTeam']}")

# Seed standings
standings_table = dynamodb.Table('nfl-standings')
standings = [
    {'teamId': 'Chiefs', 'wins': 11, 'losses': 1, 'conference': 'AFC'},
    {'teamId': 'Ravens', 'wins': 10, 'losses': 2, 'conference': 'AFC'},
    {'teamId': '49ers', 'wins': 10, 'losses': 2, 'conference': 'NFC'},
    {'teamId': 'Cowboys', 'wins': 9, 'losses': 3, 'conference': 'NFC'},
    {'teamId': 'Eagles', 'wins': 9, 'losses': 3, 'conference': 'NFC'},
]

for team in standings:
    standings_table.put_item(Item=team)
    print(f"Added: {team['teamId']}")

print("\nDone! Test data loaded.")