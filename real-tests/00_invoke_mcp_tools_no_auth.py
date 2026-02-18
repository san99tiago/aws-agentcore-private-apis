import requests
import json

CLIENT_ID = "<YOUR_CLIENT_ID>"
CLIENT_SECRET = "<YOUR_CLIENT_SECRET>"
TOKEN_URL = "<TOKEN_ENDPOINT>"


def fetch_access_token(client_id, client_secret, token_url):
    response = requests.post(
        token_url,
        data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(
            client_id=client_id, client_secret=client_secret
        ),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    return response.json()["access_token"]


def list_tools(gateway_url, access_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    payload = {"jsonrpc": "2.0", "id": "list-tools-request", "method": "tools/list"}

    response = requests.post(gateway_url, headers=headers, json=payload)
    return response.json()


# Example usage
gateway_url = "https://gateway-agentcore-bancolombia-outbound-tools-01-tv4ln7k9gd.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
# access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
access_token = "NONE"
tools = list_tools(gateway_url, access_token)
print(json.dumps(tools, indent=2))
