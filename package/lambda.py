import json

def handler(event, context):
    print("Received event:", event)

    response = {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Hello from Lambda!",
            "input": event
        })
    }

    return response
