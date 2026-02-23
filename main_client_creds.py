from universal_client import UniversalAPIClient
from dotenv import dotenv_values

# Load .env
env = dotenv_values(".env") 

# ---------------------------------
# CONFIG for API Key authentication
# ---------------------------------
"""config = {
    "auth_type": "api_key",
    "api_key": env.get("api_key"),
    "location": "header",      # could be "query" or "header" depending on API requirements, API key query param ma pathaucha ki header ma pathaucha bhanne kura API documentation ma hernu parcha
    "name": "Authorization",        # depends on API docs, weather API expects "appid" as query param for API key
    "extra_headers": {                # optional, if you want to add any extra headers for all requests
        "Accept": "application/json"
    }
}"""
""" For client creds configuration; sample config:"""
config = {
    "auth_type": "client_credentials",
    "token_url": env.get("token_url"),
    "client_id": env.get("client_id"),
    "client_secret": env.get("client_secret") 
}
# ---------------------------------
# Create client
# ---------------------------------
client = UniversalAPIClient(
    # base_url=env.get("base_url"),
    base_url=env.get("client_base_url"),
    auth_config=config
)

# ---------------------------------
# Call API
# ---------------------------------

# response = client.get_all("/orders", params={"max": 5}, limit_field="max")

response = client.get("/search",
    params={
        "q": "drake",
        "type": "artist",
        "limit": 3
    }, limit_field="limit") 

# if no params, then you can opt that out hai and just send /weather or other endpoint, whatever it is, depending on your API
print(response)