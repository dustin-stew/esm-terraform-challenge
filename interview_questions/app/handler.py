def lambda_handler(event, context):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"Processing file: s3://{bucket}/{key}")
    return {"statusCode": 200, "body": "Processed"}


# ------------------------------------------------------------------------------
# Challenge 3: Pipeline functions
# ------------------------------------------------------------------------------

def drain_queue(event, context):
    """Pull all messages from SQS and return file references for Map state."""
    sqs = boto3.client(
        'sqs',
        endpoint_url=f'http://{os.environ.get("LOCALSTACK_HOSTNAME", "localhost")}:4566',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    queue_url = os.environ['QUEUE_URL']
    files = []

    while True:
        resp = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
        messages = resp.get('Messages', [])
        if not messages:
            break
        for msg in messages:
            body = json.loads(msg['Body'])
            for record in body.get('Records', []):
                files.append({
                    'bucket': record['s3']['bucket']['name'],
                    'key': record['s3']['object']['key']
                })
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=msg['ReceiptHandle'])

    return {'messageCount': len(files), 'files': files}


def process_file(event, context):
    """Process a single file from S3."""
    bucket = event['bucket']
    key = event['key']
    print(f"Processing s3://{bucket}/{key}")
    return {'status': 'success', 'file': key}


def notify(event, context):
    """Send summary notification via SNS."""
    sns = boto3.client(
        'sns',
        endpoint_url=f'http://{os.environ.get("LOCALSTACK_HOSTNAME", "localhost")}:4566',
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    topic_arn = os.environ['SNS_TOPIC_ARN']
    message = json.dumps(event, default=str)
    sns.publish(TopicArn=topic_arn, Message=message, Subject='Pipeline Result')
    return {'status': 'notified'}



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


# ------------------------------------------------------------------------------
# Challenge 4: WebSocket handlers
# ------------------------------------------------------------------------------

def ws_connect(event, context):
    """Store connectionId when a client connects."""
    connection_id = event['requestContext']['connectionId']
    table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])
    table.put_item(Item={'connectionId': connection_id})
    return {'statusCode': 200}


def ws_disconnect(event, context):
    """Remove connectionId when a client disconnects."""
    connection_id = event['requestContext']['connectionId']
    table = dynamodb.Table(os.environ['CONNECTIONS_TABLE'])
    table.delete_item(Key={'connectionId': connection_id})
    return {'statusCode': 200}


def ws_default(event, context):
    """No-op for unsupported routes."""
    return {'statusCode': 200}


def ws_broadcast(event, context):
    """Broadcast DynamoDB Stream changes to all connected WebSocket clients."""
    table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'nfl-ws-connections'))
    ws_endpoint = os.environ.get('WS_ENDPOINT', '')

    # For LocalStack, use the LocalStack endpoint
    if 'LOCALSTACK_HOSTNAME' in os.environ:
        api_url = f'http://{os.environ["LOCALSTACK_HOSTNAME"]}:4566'
    else:
        api_url = ws_endpoint

    apigw = boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=api_url,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

    # Build payload from stream records
    changes = []
    for record in event.get('Records', []):
        if record.get('eventName') in ('INSERT', 'MODIFY'):
            new_image = record['dynamodb'].get('NewImage', {})
            # Convert DynamoDB format to plain dict
            item = {}
            for k, v in new_image.items():
                if 'S' in v:
                    item[k] = v['S']
                elif 'N' in v:
                    item[k] = int(v['N']) if '.' not in v['N'] else float(v['N'])
            changes.append(item)

    if not changes:
        return {'statusCode': 200}

    message = json.dumps({'type': 'update', 'data': changes})

    # Send to all connected clients
    connections = table.scan().get('Items', [])
    for conn in connections:
        try:
            apigw.post_to_connection(
                ConnectionId=conn['connectionId'],
                Data=message
            )
        except Exception:
            # Stale connection — clean up
            table.delete_item(Key={'connectionId': conn['connectionId']})

    return {'statusCode': 200}