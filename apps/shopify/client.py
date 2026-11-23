import re

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured


class ShopifyAPIError(Exception):
    """Raised when communication with Shopify fails."""
    pass


class ShopifyClient:

    def __init__(self):

        self.shop = self._get_shop_domain()

        self.client_id = settings.SHOPIFY_CLIENT_ID
        self.client_secret = settings.SHOPIFY_CLIENT_SECRET
        self.api_version = settings.SHOPIFY_API_VERSION

        if not all((self.client_id, self.client_secret)):
            raise ImproperlyConfigured(
                "Shopify credentials are missing."
            )

        if not re.fullmatch(r"\d{4}-\d{2}", self.api_version):
            raise ImproperlyConfigured(
                "SHOPIFY_API_VERSION must use YYYY-MM format."
            )

        self.base_url = (
            f"https://{self.shop}/admin/api/{self.api_version}"
        )

    @staticmethod
    def _get_shop_domain():

        shop = settings.SHOPIFY_SHOP.strip().lower()

        if shop.endswith(".myshopify.com"):
            domain = shop
        else:
            domain = f"{shop}.myshopify.com"

        pattern = (
            r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
            r"\.myshopify\.com"
        )

        if not re.fullmatch(pattern, domain):
            raise ImproperlyConfigured(
                "SHOPIFY_SHOP must be a valid Shopify store domain."
            )

        return domain

    # --------------------------------------------------
    # ACCESS TOKEN
    # --------------------------------------------------

    def get_access_token(self):

        token_cache_key = (
            f"shopify_access_token:{self.shop}:{self.client_id}"
        )

        token = cache.get(token_cache_key)

        if token:
            return token

        url = f"https://{self.shop}/admin/oauth/access_token"

        try:

            response = requests.post(
                url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=20,
            )

            response.raise_for_status()

            data = response.json()

        except requests.RequestException as error:

            raise ShopifyAPIError(
                "Shopify token request failed."
            ) from error

        except ValueError as error:

            raise ShopifyAPIError(
                "Shopify returned an invalid token response."
            ) from error

        if not isinstance(data, dict):
            raise ShopifyAPIError(
                "Invalid Shopify token response."
            )

        token = data.get("access_token")

        if not isinstance(token, str) or not token:
            raise ShopifyAPIError(
                "Shopify did not return an access token."
            )

        expires_in = data.get(
            "expires_in",
            23 * 60 * 60 + 60,
        )

        if isinstance(expires_in, int) and not isinstance(expires_in, bool):

            cache.set(
                token_cache_key,
                token,
                timeout=max(expires_in - 60, 1),
            )

        return token

    # --------------------------------------------------
    # GRAPHQL CLIENT
    # --------------------------------------------------

    def graphql(self, query, variables=None):

        url = f"{self.base_url}/graphql.json"

        try:

            response = requests.post(
                url,
                json={
                    "query": query,
                    "variables": variables or {},
                },
                headers={
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": self.get_access_token(),
                },
                timeout=30,
            )

            response.raise_for_status()

            result = response.json()

        except requests.RequestException as error:

            raise ShopifyAPIError(
                "Shopify GraphQL request failed."
            ) from error

        except ValueError as error:

            raise ShopifyAPIError(
                "Shopify returned invalid JSON."
            ) from error

        if not isinstance(result, dict):
            raise ShopifyAPIError(
                "Invalid Shopify GraphQL response."
            )

        if result.get("errors"):

            raise ShopifyAPIError(
                f"Shopify GraphQL errors: {result['errors']}"
            )

        data = result.get("data")

        if not isinstance(data, dict):
            raise ShopifyAPIError(
                "Shopify response does not contain valid data."
            )

        return data

    # --------------------------------------------------
    # CONNECTION TEST
    # --------------------------------------------------

    def test_connection(self):

        data = self.graphql(
            """
            query ShopifyConnectionTest {
                shop {
                    name
                    myshopifyDomain
                }
            }
            """
        )

        shop = data.get("shop")

        if not isinstance(shop, dict) or not shop.get("name"):
            raise ShopifyAPIError(
                "Shopify did not return shop information."
            )

        return shop