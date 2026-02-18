"""Lambda handler for Investment Products API.

Routes:
    GET /investments/{username} -> query investment products by username (PK=USER#{username})
"""

import json
import os
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    try:
        table_name = os.environ["TABLE_NAME"]
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        path_parameters = event.get("pathParameters") or {}
        username = path_parameters.get("username")

        if not username:
            return build_response(
                400, {"message": "Missing required parameter: username"}
            )

        response = table.query(KeyConditionExpression=Key("PK").eq(f"USER#{username}"))
        items = response.get("Items", [])

        if not items:
            return build_response(
                404, {"message": f"No investment products found for user: {username}"}
            )

        return build_response(
            200, {"investments": items, "username": username, "count": len(items)}
        )

    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return build_response(500, {"message": f"Internal server error: {str(e)}"})
