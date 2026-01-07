"""
Enterprise SSO/SAML Support

Provides SAML 2.0 and OIDC authentication for enterprise customers.

@ai_prompt: Configure SSO with environment variables or config file
@context_boundary: aegistwin/security/sso

# AI-GENERATED 2026-01-07
"""

import os
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    HAS_SAML = True
except ImportError:
    HAS_SAML = False


@dataclass
class SAMLConfig:
    """SAML 2.0 configuration."""
    entity_id: str
    sso_url: str
    slo_url: str | None = None
    x509_cert: str | None = None
    sp_entity_id: str = "aegistwin"
    sp_acs_url: str = "http://localhost:8000/auth/saml/acs"
    sp_sls_url: str = "http://localhost:8000/auth/saml/sls"


@dataclass
class OIDCConfig:
    """OpenID Connect configuration."""
    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8000/auth/oidc/callback"
    scopes: list[str] = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = ["openid", "profile", "email"]


class SAMLProvider:
    """
    SAML 2.0 authentication provider.
    
    Supports enterprise SSO with Okta, Azure AD, OneLogin, etc.
    
    Usage:
        provider = SAMLProvider(config)
        auth_url = provider.get_login_url()
        user = provider.validate_response(request)
    """
    
    def __init__(self, config: SAMLConfig):
        if not HAS_SAML:
            raise RuntimeError(
                "python3-saml not installed. Install with: pip install python3-saml"
            )
        
        self.config = config
        self._settings = self._build_settings()
    
    def _build_settings(self) -> dict:
        """Build SAML settings dictionary."""
        return {
            "strict": True,
            "debug": os.getenv("SAML_DEBUG", "false").lower() == "true",
            "sp": {
                "entityId": self.config.sp_entity_id,
                "assertionConsumerService": {
                    "url": self.config.sp_acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },
                "singleLogoutService": {
                    "url": self.config.sp_sls_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified",
            },
            "idp": {
                "entityId": self.config.entity_id,
                "singleSignOnService": {
                    "url": self.config.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "singleLogoutService": {
                    "url": self.config.slo_url or self.config.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": self.config.x509_cert or "",
            },
        }
    
    def prepare_request(self, request: Request) -> dict:
        """Prepare request data for SAML library."""
        return {
            "https": "on" if request.url.scheme == "https" else "off",
            "http_host": request.url.hostname,
            "server_port": request.url.port,
            "script_name": request.url.path,
            "get_data": dict(request.query_params),
            "post_data": {},
        }
    
    def get_login_url(self, request: Request, return_to: str | None = None) -> str:
        """Get SSO login URL."""
        req = self.prepare_request(request)
        auth = OneLogin_Saml2_Auth(req, self._settings)
        return auth.login(return_to=return_to)
    
    async def validate_response(self, request: Request) -> dict[str, Any]:
        """Validate SAML response and extract user data."""
        req = self.prepare_request(request)
        req["post_data"] = dict(await request.form())
        
        auth = OneLogin_Saml2_Auth(req, self._settings)
        auth.process_response()
        
        errors = auth.get_errors()
        if errors:
            raise HTTPException(status_code=401, detail=f"SAML error: {', '.join(errors)}")
        
        if not auth.is_authenticated():
            raise HTTPException(status_code=401, detail="SAML authentication failed")
        
        attributes = auth.get_attributes()
        
        return {
            "name_id": auth.get_nameid(),
            "session_index": auth.get_session_index(),
            "attributes": attributes,
            "email": attributes.get("email", [None])[0],
            "name": attributes.get("name", [None])[0],
            "groups": attributes.get("groups", []),
        }


class OIDCProvider:
    """
    OpenID Connect authentication provider.
    
    Supports Auth0, Okta, Azure AD, Google, etc.
    
    Usage:
        provider = OIDCProvider(config)
        auth_url = provider.get_authorization_url()
        user = await provider.exchange_code(code)
    """
    
    def __init__(self, config: OIDCConfig):
        self.config = config
        self._discovery_url = f"{config.issuer}/.well-known/openid-configuration"
        self._discovery_cache: dict | None = None
    
    async def _get_discovery_document(self) -> dict:
        """Fetch OIDC discovery document."""
        if self._discovery_cache:
            return self._discovery_cache
        
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(self._discovery_url)
            response.raise_for_status()
            self._discovery_cache = response.json()
            return self._discovery_cache
    
    def get_authorization_url(self, state: str) -> str:
        """Get OAuth2 authorization URL."""
        import urllib.parse
        
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "state": state,
        }
        
        # For initial implementation, construct manually
        # In production, use discovery document
        auth_endpoint = f"{self.config.issuer}/authorize"
        return f"{auth_endpoint}?{urllib.parse.urlencode(params)}"
    
    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        import httpx
        
        discovery = await self._get_discovery_document()
        token_endpoint = discovery.get("token_endpoint")
        
        if not token_endpoint:
            # Fallback
            token_endpoint = f"{self.config.issuer}/oauth/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_endpoint, data=data)
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user info from OIDC provider."""
        import httpx
        
        discovery = await self._get_discovery_document()
        userinfo_endpoint = discovery.get("userinfo_endpoint")
        
        if not userinfo_endpoint:
            # Fallback
            userinfo_endpoint = f"{self.config.issuer}/userinfo"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_endpoint, headers=headers)
            response.raise_for_status()
            return response.json()


def create_saml_provider_from_env() -> SAMLProvider | None:
    """Create SAML provider from environment variables."""
    entity_id = os.getenv("SAML_IDP_ENTITY_ID")
    sso_url = os.getenv("SAML_IDP_SSO_URL")
    
    if not (entity_id and sso_url):
        return None
    
    config = SAMLConfig(
        entity_id=entity_id,
        sso_url=sso_url,
        slo_url=os.getenv("SAML_IDP_SLO_URL"),
        x509_cert=os.getenv("SAML_IDP_X509_CERT"),
        sp_entity_id=os.getenv("SAML_SP_ENTITY_ID", "aegistwin"),
        sp_acs_url=os.getenv("SAML_SP_ACS_URL", "http://localhost:8000/auth/saml/acs"),
        sp_sls_url=os.getenv("SAML_SP_SLS_URL", "http://localhost:8000/auth/saml/sls"),
    )
    
    return SAMLProvider(config)


def create_oidc_provider_from_env() -> OIDCProvider | None:
    """Create OIDC provider from environment variables."""
    issuer = os.getenv("OIDC_ISSUER")
    client_id = os.getenv("OIDC_CLIENT_ID")
    client_secret = os.getenv("OIDC_CLIENT_SECRET")
    
    if not (issuer and client_id and client_secret):
        return None
    
    scopes_str = os.getenv("OIDC_SCOPES", "openid profile email")
    scopes = scopes_str.split()
    
    config = OIDCConfig(
        issuer=issuer,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=os.getenv("OIDC_REDIRECT_URI", "http://localhost:8000/auth/oidc/callback"),
        scopes=scopes,
    )
    
    return OIDCProvider(config)
