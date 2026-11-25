"""How the OpenAPI schema describes the cookie authentication."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class JWTCookieScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.JWTCookieAuthentication"
    name = "cookieAuth"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "cookie", "name": "access_token"}
