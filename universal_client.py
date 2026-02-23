import requests
import time

# ==================================
# Pagination Strategy
# ==================================
class PaginationStrategy:
    OFFSET = "offset"           # offset + limit
    PAGE = "page"               # page + per_page
    HAS_MORE = "has_more"       # boolean flag

# ==================================
# Base Authentication
# ==================================
class BaseAuth:
    def get_auth_data(self):
        """
        Returns dictionary:
        {
            "headers": {},
            "params": {}
        }
        """
        return {"headers": {}, "params": {}}


# ==================================
# API Key Authentication
# ==================================
class APIKeyAuth(BaseAuth):
    def __init__(self, api_key, location="header", name="x-api-key", extra_headers=None):
        """
        location: 'header' or 'query'
        name: header name OR query param name
        extra_headers: dict of any additional headers to include in every request
        """
        self.api_key = api_key
        self.location = location
        self.name = name
        self.extra_headers = extra_headers or {}


    def get_auth_data(self):
        if self.location == "header":
            headers = {self.name: self.api_key}
            headers.update(self.extra_headers)  # merge extra headers
            return {"headers": headers, "params": {}}

        elif self.location == "query":
            return {
                "headers": self.extra_headers,  # kaile kai esma ni headers pathauna parne huncha, depending on API requirements
                "params": {self.name: self.api_key}
            }

        else:
            raise ValueError("Invalid API key location")


# ==================================
# Client Credentials Authentication
# ==================================
class ClientCredentialsAuth(BaseAuth):
    def __init__(self, token_url, client_id, client_secret):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.expiry_time = 0

    def _authenticate(self):
        print("Fetching new token...")

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials"
            },
            auth=(self.client_id, self.client_secret)
        )

        response.raise_for_status()
        token_data = response.json()

        self.access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)

        self.expiry_time = time.time() + expires_in

    def force_refresh(self):
        self.access_token = None
        self.expiry_time = 0
        self._authenticate()

    def get_auth_data(self):
        if not self.access_token or time.time() >= self.expiry_time:
            self._authenticate()

        return {
            "headers": {"Authorization": f"Bearer {self.access_token}"},
            "params": {}
        }


# ==================================
# Universal API Client
# ==================================
class UniversalAPIClient:
    def __init__(self, base_url, auth_config):
        self.base_url = base_url.rstrip("/")
        self.auth = self._create_auth(auth_config)

    def _create_auth(self, config):
        auth_type = config.get("auth_type")

        if auth_type == "api_key":
            return APIKeyAuth(
                api_key=config["api_key"],
                location=config.get("location", "header"),
                name=config.get("name", "x-api-key"),
                extra_headers=config.get("extra_headers", {})  # <-- support extra_headers
            )

        elif auth_type == "client_credentials":
            return ClientCredentialsAuth(
                token_url=config["token_url"],
                client_id=config["client_id"],
                client_secret=config["client_secret"]
            )

        else:
            raise ValueError("Unsupported auth type")

    def _make_request(self, method, endpoint, params=None, **kwargs):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        auth_data = self.auth.get_auth_data()

        headers = auth_data.get("headers", {})
        auth_params = auth_data.get("params", {})

        final_params = {}
        if params:
            final_params.update(params)
        final_params.update(auth_params)

        response = requests.request(
            method,
            url,
            headers=headers,
            params=final_params,
            **kwargs
        )

        # DEBUGGING LOGS
        # print("URL:", url)
        # print("Headers:", headers)
        # print("Params:", final_params)

        # Retry once on 401 for OAuth
        if response.status_code == 401 and isinstance(self.auth, ClientCredentialsAuth):
            print("401 received. Refreshing token...")
            self.auth.force_refresh()

            auth_data = self.auth.get_auth_data()
            headers = auth_data.get("headers", {})

            response = requests.request(
                method,
                url,
                headers=headers,
                params=final_params,
                **kwargs
            )

        response.raise_for_status()
        return response

    def get(self, endpoint, params=None):
        return self._make_request("GET", endpoint, params=params).json()

    def post(self, endpoint, json=None):
        return self._make_request("POST", endpoint, json=json).json()
    
    # ==================================
    # Fetch all paginated records
    # ==================================

    """Offset / Limit – keeps fetching until fewer than limit records are returned. 

    Page / Per-Page – increments page until total_pages is reached (or no data is returned). 

    Has-More Flag – loops until has_more is False. """

    def get_all(self, endpoint, params=None, headers=None,
                strategy=PaginationStrategy.OFFSET,
                limit_field="limit", offset_field="offset",
                page_field="page", per_page_field="per_page",
                has_more_field="has_more"):
        results = []
        params = params.copy() if params else {}

        if strategy == PaginationStrategy.OFFSET:
            offset = 0
            limit = params.get(limit_field, 50)
            total_count = None

            while True:
                params[offset_field] = offset
                response = self.get(endpoint, params=params)
                data = response.get("orders", [])
                print(f"Fetching offset {offset} (limit={limit}), fetched {len(data)} records")
                results.extend(data)
                
                # set total_count from first response
                if total_count is None:
                    total_count = response.get("total_count", None)
                
                offset += limit
                
                # stop conditions
                if offset >= 25:  # breaking at offset 25 for test purpose
                    break
                if total_count is not None and offset >= total_count:
                    break
                if not data:  # safety check
                    break

        elif strategy == PaginationStrategy.PAGE:
            page = 1
            per_page = params.get(per_page_field, 50)
            while True:
                params[page_field] = page
                response = self.get(endpoint, params=params)
                data = response.get("orders", [])
                print(f"Fetching page {page} (per_page={per_page}), fetched {len(data)} records")
                results.extend(data)
                total_pages = response.get("total_pages")

                if page > 3: # breaking at page 3 for test purpose
                    break

                if total_pages is not None:
                    if page >= total_pages:
                        break
                elif not data:
                    break
                page += 1

        elif strategy == PaginationStrategy.HAS_MORE:
            has_more = True
            iteration = 0
            while has_more:
                response = self.get(endpoint, params=params)
                data = response.get("orders", [])
                iteration += 1
                print(f"Iteration {iteration}, fetched {len(data)} records")
                results.extend(data)
                has_more = response.get(has_more_field, False)

                # stopping at 3rd iteration for test purpose
                if iteration >= 3:
                    break
        return results