# Universal API Client

A reusable Python API client that supports:

- API key authentication (`header` or `query`)
- OAuth2 Client Credentials authentication (auto token refresh)
- Basic `GET` and `POST` requests
- Paginated fetch via multiple pagination strategies

## Project Structure

- `universal_client.py` → client, auth classes, pagination strategies
- `main.py` → example usage with `.env`
- `.env` / `.env.sample` → runtime configuration

## Requirements

- Python 3.8+
- `requests`
- `python-dotenv`

Install dependencies:

```bash
pip install requests python-dotenv
```

## Environment Variables

Based on current `main.py`, the following keys are expected in `.env`:

```env
base_url=https://api.example.com
api_key=YOUR_API_KEY
```

## Authentication Modes

### 1) API Key Auth

Use `auth_type="api_key"` with:

- `api_key`
- `location` (`header` or `query`)
- `name` (header/query parameter name)
- optional `extra_headers`

Example:

```python
config = {
	"auth_type": "api_key",
	"api_key": env.get("api_key"),
	"location": "header",
	"name": "Authorization",
	"extra_headers": {
		"Accept": "application/json"
	}
}
```

### 2) OAuth2 Client Credentials

Use `auth_type="client_credentials"` with:

- `token_url`
- `client_id`
- `client_secret`

The client automatically fetches a token and retries once on `401` by refreshing it.

## Usage

Current implementation expects data in `response["orders"]` for pagination loops.

## Important Notes (Current Code Behavior)

In `universal_client.py`, pagination loops currently include test break conditions:

- OFFSET stops when `offset >= 25`
- PAGE stops when `page > 3`
- HAS_MORE stops at `iteration >= 3`

These are useful for testing but will limit full data retrieval in production.

## Run Example

```bash
python main.py
```