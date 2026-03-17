def lambda_handler(event, context):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"Processing file: s3://{bucket}/{key}")
    return {"statusCode": 200, "body": "Processed"}




import json
import os
from decimal import Decimal
import boto3


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)

endpoint = os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url=f'http://{endpoint}:4566',
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
        'body': json.dumps(response.get('Items', []), cls=DecimalEncoder)
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
        'body': json.dumps(response.get('Items', []), cls=DecimalEncoder)
    }