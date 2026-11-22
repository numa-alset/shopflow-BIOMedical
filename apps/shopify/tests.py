# from unittest.mock import patch

# from django.test import TestCase, override_settings
# from rest_framework.test import APIClient

# from .client import ShopifyAPIError, ShopifyClient


# @override_settings(
#     SHOPIFY_SHOP="example-store",
#     SHOPIFY_CLIENT_ID="client-id",
#     SHOPIFY_CLIENT_SECRET="client-secret",
#     SHOPIFY_API_VERSION="2026-10",
# )
# class ShopifyClientTests(TestCase):
#     @patch("apps.shopify.client.requests.post")
#     def test_connection_fetches_shop_information(self, post):
#         post.return_value.json.side_effect = [
#             {"access_token": "access-token", "expires_in": 86400},
#             {
#                 "data": {
#                     "shop": {
#                         "name": "Example Store",
#                         "myshopifyDomain": "example-store.myshopify.com",
#                     }
#                 }
#             },
#         ]

#         shop = ShopifyClient().test_connection()

#         self.assertEqual(shop["name"], "Example Store")
#         self.assertEqual(post.call_count, 2)
#         self.assertIn(
#             "https://example-store.myshopify.com/admin/api/2026-10/graphql.json",
#             post.call_args_list[1].args,
#         )

#     @patch("apps.shopify.client.requests.post")
#     def test_graphql_errors_raise_shopify_api_error(self, post):
#         post.return_value.json.side_effect = [
#             {"access_token": "access-token", "expires_in": 86400},
#             {"errors": [{"message": "Access denied"}]},
#         ]

#         with self.assertRaises(ShopifyAPIError):
#             ShopifyClient().test_connection()


# @override_settings(
#     SHOPIFY_SHOP="example-store",
#     SHOPIFY_CLIENT_ID="client-id",
#     SHOPIFY_CLIENT_SECRET="client-secret",
#     SHOPIFY_API_VERSION="2026-10",
# )
# class ShopifyConnectionViewTests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user = self._create_user()

#     @staticmethod
#     def _create_user():
#         from django.contrib.auth import get_user_model

#         return get_user_model().objects.create_user(
#             username="shopify-test-user",
#             password="test-password",
#         )

#     @patch("apps.shopify.views.ShopifyClient.test_connection")
#     def test_authenticated_user_can_test_connection(self, test_connection):
#         self.client.force_authenticate(user=self.user)
#         test_connection.return_value = {
#             "name": "Example Store",
#             "myshopifyDomain": "example-store.myshopify.com",
#         }

#         response = self.client.post("/api/shopify/test-connection/")

#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(response.data["connected"])
#         test_connection.assert_called_once_with()

#     @patch("apps.shopify.views.ShopifyClient.test_connection")
#     def test_connection_test_requires_authentication(self, test_connection):
#         response = self.client.post("/api/shopify/test-connection/")

#         self.assertEqual(response.status_code, 401)
#         test_connection.assert_not_called()
