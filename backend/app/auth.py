import os
from dataclasses import dataclass
from typing import Any

import jwt
from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

load_dotenv()

security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    claims: dict[str, Any]
    token: str


@dataclass(frozen=True)
class AuthContext:
    user_id: str | None
    claims: dict[str, Any]
    token: str | None
    is_internal: bool = False


def _get_jwks_client() -> PyJWKClient:
    jwks_url = os.getenv("CLERK_JWKS_URL")
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_JWKS_URL is not configured",
        )
    return PyJWKClient(jwks_url)


def _verify_clerk_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = credentials.credentials

    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        ) from exc

    authorized_party = os.getenv("CLERK_AUTHORIZED_PARTY")
    if authorized_party and claims.get("azp") != authorized_party:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorized party",
        )

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing subject",
        )

    return CurrentUser(user_id=user_id, claims=claims, token=token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    return _verify_clerk_credentials(credentials)


def get_internal_api_key(
    x_internal_api_key: str | None = Header(
        default=None,
        alias="X-Internal-API-Key",
    ),
) -> str:
    internal_api_key = os.getenv("INTERNAL_API_KEY")
    if not internal_api_key or x_internal_api_key != internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )
    return x_internal_api_key


def get_current_user_or_internal(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_internal_api_key: str | None = Header(
        default=None,
        alias="X-Internal-API-Key",
    ),
) -> AuthContext:
    internal_api_key = os.getenv("INTERNAL_API_KEY")
    if x_internal_api_key is not None:
        if not internal_api_key or x_internal_api_key != internal_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid internal API key",
            )
        return AuthContext(
            user_id=None,
            claims={},
            token=None,
            is_internal=True,
        )

    current_user = _verify_clerk_credentials(credentials)
    return AuthContext(
        user_id=current_user.user_id,
        claims=current_user.claims,
        token=current_user.token,
        is_internal=False,
    )
