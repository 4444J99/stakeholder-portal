"""Authentication middleware for the API gateway.

Three auth strategies that stack (first match wins):
1. Local bypass — requests from 127.0.0.1 / ::1 skip auth
2. Cloudflare Access JWT — validates Cf-Access-Jwt-Assertion header
3. API key — X-API-Key header matched against ORGANVM_API_KEY env var
"""

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

_CF_CERTS_URL = "https://{team_domain}/cdn-cgi/access/certs"
_cf_public_keys: list[dict[str, Any]] = []

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _is_local(request: Request) -> bool:
    """Check if the request originates from localhost."""
    client = request.client
    if client is None:
        return False
    return client.host in ("127.0.0.1", "::1", "localhost")


async def _get_cf_public_keys(team_domain: str) -> list[dict[str, Any]]:
    """Fetch and cache Cloudflare Access public keys."""
    global _cf_public_keys
    if _cf_public_keys:
        return _cf_public_keys

    url = _CF_CERTS_URL.format(team_domain=team_domain)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
        _cf_public_keys = resp.json().get("keys", [])
    return _cf_public_keys


def _verify_cf_jwt(token: str, team_domain: str, audience: str) -> dict[str, Any] | None:  # allow-secret
    """Verify a Cloudflare Access JWT. Returns claims or None."""
    try:
        # Fetch keys synchronously from cache (populated at first request)
        if not _cf_public_keys:
            return None

        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        for key_data in _cf_public_keys:
            if key_data.get("kid") == kid:
                # CF Access JWKs are always public keys; cast for pyright
                public_key = cast(Any, RSAAlgorithm.from_jwk(key_data))
                return jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    audience=audience,
                    options={"verify_exp": True},
                )
    except (jwt.InvalidTokenError, KeyError, ValueError):
        pass
    return None


async def require_api_auth(
    request: Request,
    api_key: str | None = Security(api_key_header),  # allow-secret
) -> dict[str, Any]:
    """FastAPI dependency that enforces authentication.

    Returns a dict with auth metadata: {"method": "local"|"cf_jwt"|"api_key", ...}
    """
    # 1. Local bypass
    if _is_local(request):
        return {"method": "local", "identity": "localhost"}

    # 2. Cloudflare Access JWT
    cf_team_domain = os.environ.get("CF_ACCESS_TEAM_DOMAIN", "")
    cf_audience = os.environ.get("CF_ACCESS_AUDIENCE", "")
    cf_jwt = request.headers.get("Cf-Access-Jwt-Assertion")

    if cf_jwt and cf_team_domain and cf_audience:
        # Ensure keys are cached
        await _get_cf_public_keys(cf_team_domain)
        claims = _verify_cf_jwt(cf_jwt, cf_team_domain, cf_audience)
        if claims:
            return {
                "method": "cf_jwt",
                "identity": claims.get("email", "unknown"),
            }

    # 3. API key
    expected_key = os.environ.get("ORGANVM_API_KEY", "")
    if api_key and expected_key and api_key == expected_key:  # allow-secret
        return {"method": "api_key", "identity": "api_key_holder"}

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide X-API-Key header or use Cloudflare Access.",
    )
