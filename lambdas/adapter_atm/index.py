"""
Lambda Adapter for ATM Machines Health Private API.
Acts as a proxy so AgentCore Gateway can reach the Private API via Lambda target.
"""

import json
import os
import logging
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_BASE_URL = os.environ.get("API_BASE_URL", "")


def handler(event, context):
    """Proxy handler that forwards requests to the Private ATM Machines Health API.

    Supports:
        - list_atms() -> GET /atms
        - list_atms_by_city(city) -> GET /atms/{city}
    """
    logger.info("Adapter received event: %s", json.dumps(event))

    try:
        city = event.get("city")

        if city:
            url = f"{API_BASE_URL}/atms/{city}"
        else:
            url = f"{API_BASE_URL}/atms"

        logger.info("Proxying request to: %s", url)

        req = Request(url, method="GET")
        req.add_header("Content-Type", "application/json")

        with urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            status_code = response.status

        logger.info("Private API responded with status: %s", status_code)
        return json.loads(body)

    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        logger.error("HTTP error from Private API: %s - %s", e.code, error_body)
        return {"error": f"Private API returned {e.code}", "details": error_body}

    except URLError as e:
        logger.error("Connection error to Private API: %s", str(e))
        return {"error": "Cannot reach Private API", "details": str(e)}

    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return {"error": "Internal adapter error", "details": str(e)}
