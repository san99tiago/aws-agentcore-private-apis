import json
import os
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles DynamoDB Decimal types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def build_response(status_code, body):
    """Build an API Gateway compatible response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def handler(event, context):
    """Lambda handler for ATM machines health API.

    Routes:
        GET /atms        -> scan all ATMs
        GET /atms/{city} -> query ATMs by city (PK=CITY#{city})
    """
    logger.info("Received event: %s", json.dumps(event))

    try:
        table_name = os.environ["TABLE_NAME"]
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        path_parameters = event.get("pathParameters") or {}
        city = path_parameters.get("city")

        if city:
            response = table.query(KeyConditionExpression=Key("PK").eq(f"CITY#{city}"))
            items = response.get("Items", [])

            if not items:
                return build_response(
                    404, {"message": f"No ATMs found for city: {city}"}
                )
        else:
            response = table.scan()
            items = response.get("Items", [])

        return build_response(200, {"atms": items, "count": len(items)})

    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return build_response(500, {"message": f"Internal server error: {str(e)}"})
