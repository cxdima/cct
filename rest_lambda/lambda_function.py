import json
from decimal import Decimal
import boto3

LOCATIONS_TABLE = boto3.resource("dynamodb").Table("locations")


def get_locations_handler(event):
    try:
        items = LOCATIONS_TABLE.scan()["Items"]
        return respond(200, items)
    except Exception as e:
        return respond(500, {"error": str(e)})


def test_handler(event):
    return respond(200, {"message": "OK"})


ROUTE_HANDLERS = {
    ("GET", "/locations"): get_locations_handler,
    ("GET", "/test"): test_handler
}


def lambda_handler(event, context):
    http = event["requestContext"]["http"]
    method = http["method"]
    path = event["rawPath"]

    if method == "OPTIONS":
        return respond(200, {})

    handler = ROUTE_HANDLERS.get((method, path))
    if handler:
        return handler(event)

    return respond(404, {"error": "Not Found"})


def decimal_converter(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"{value!r} is not JSON serializable")


def respond(status, data):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(data, default=decimal_converter)
    }
