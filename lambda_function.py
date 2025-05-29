import datetime
import json
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('cct-telegram-users')

status_check_path = '/status'
auth_path = '/telegram-auth'

def lambda_handler(event, context):
    try:
        http_method = event.get('httpMethod')
        path = event.get('path')

        if http_method == 'OPTIONS':
            return build_response(200, {})
        elif http_method == 'GET' and path == status_check_path:
            return build_response(200, 'Service is operational')
        elif http_method == 'GET' and path == '/test':
            return build_response(200, 'Test endpoint')
        elif http_method == 'POST' and path == auth_path:
            return handle_telegram_auth(event)
        else:
            return build_response(404, 'Not Found')
    except Exception as e:
        return build_response(400, f'Error processing request: {str(e)}')

def handle_telegram_auth(event):
    try:
        body = json.loads(event.get('body', '{}'))
        userid = body.get('userid')

        if userid is None:
            return build_response(400, 'userid is required in the request body')

        # DynamoDB expects a number, ensure it is int or float
        if not isinstance(userid, (int, float)):
            return build_response(400, 'userid must be a number')

        response = table.get_item(Key={'user_id': userid})

        item = response.get('Item')
        if item:
            return build_response(200, item)
        else:
            return build_response(404, 'User not found')

    except Exception as e:
        return build_response(500, f'Internal server error: {str(e)}')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o % 1 == 0 else float(o)
        return super(DecimalEncoder, self).default(o)

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Origin, Content-Type, X-Auth-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS,DELETE,PUT,PATCH',
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
