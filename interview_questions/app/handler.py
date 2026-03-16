def lambda_handler(event, context):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"Processing file: s3://{bucket}/{key}")
    return {"statusCode": 200, "body": "Processed"}




import json
import os
import boto3

dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:4566',
    region_name='us-east-1',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

def get_scores(event, context):
    table = dynamodb.Table(os.environ.get('SCORES_TABLE', 'nfl-scores'))
    response = table.scan()
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response.get('Items', []))
    }

def get_standings(event, context):
    table = dynamodb.Table(os.environ.get('STANDINGS_TABLE', 'nfl-standings'))
    response = table.scan()
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response.get('Items', []))
    }