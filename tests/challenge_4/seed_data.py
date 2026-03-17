import boto3
import time

# LocalStack endpoint
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

scores_table = dynamodb.Table('nfl-scores')
standings_table = dynamodb.Table('nfl-standings')

# Seed initial scores
scores = [
    {'gameId': 'game-001', 'homeTeam': 'Chiefs', 'awayTeam': 'Ravens', 'homeScore': 27, 'awayScore': 24, 'status': 'Final'},
    {'gameId': 'game-002', 'homeTeam': 'Cowboys', 'awayTeam': 'Eagles', 'homeScore': 14, 'awayScore': 21, 'status': 'Q4 2:30'},
    {'gameId': 'game-003', 'homeTeam': '49ers', 'awayTeam': 'Rams', 'homeScore': 0, 'awayScore': 0, 'status': 'Upcoming'},
]

for score in scores:
    scores_table.put_item(Item=score)
    print(f"Added: {score['homeTeam']} vs {score['awayTeam']} - {score['status']}")

# Seed initial standings
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

print("\nInitial data loaded. Starting game simulation...\n")

# --- Simulate Q4 countdown ---
seconds_left = 30
while seconds_left > 3:
    minutes = seconds_left // 60
    secs = seconds_left % 60
    status = f"Q4 {minutes}:{secs:02d}"
    scores_table.update_item(
        Key={'gameId': 'game-002'},
        UpdateExpression='SET #s = :v',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':v': status}
    )
    print(f"  Clock: {status}  |  Cowboys 14 - 21 Eagles")
    time.sleep(1)
    seconds_left -= 1

# Cowboys touchdown! 20-21
scores_table.update_item(
    Key={'gameId': 'game-002'},
    UpdateExpression='SET homeScore = :score, #s = :status',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':score': 20, ':status': 'Q4 0:03'}
)
print("\n  TOUCHDOWN COWBOYS!")
print("  Clock: Q4 0:03  |  Cowboys 20 - 21 Eagles")
print("  Going for two...\n")

# Wait for two-point conversion attempt
time.sleep(8)

# Two-point conversion good! 22-21, game over
scores_table.update_item(
    Key={'gameId': 'game-002'},
    UpdateExpression='SET homeScore = :score, #s = :status',
    ExpressionAttributeNames={'#s': 'status'},
    ExpressionAttributeValues={':score': 22, ':status': 'Final'}
)
print("  TWO-POINT CONVERSION IS GOOD!")
print("  FINAL: Cowboys 22 - 21 Eagles\n")

# Update standings
standings_table.update_item(
    Key={'teamId': 'Cowboys'},
    UpdateExpression='SET wins = :w',
    ExpressionAttributeValues={':w': 10}
)
standings_table.update_item(
    Key={'teamId': 'Eagles'},
    UpdateExpression='SET losses = :l',
    ExpressionAttributeValues={':l': 4}
)
print("  Standings updated: Cowboys 10-3, Eagles 9-4")
print("\nDone!")
