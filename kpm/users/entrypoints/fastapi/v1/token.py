import logging
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken, RefreshToken
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_refresh_token
from kpm.shared.security import salt_password, verify_password
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.adapters.memrepo import views
from kpm.users.domain.model import User
from kpm.users.entrypoints.fastapi.v1.schemas.token import LoginResponse

router = APIRouter(
    responses={404: {"description": "Not found"}}, tags=["auth"]
)

logger = logging.getLogger("kpm")


def check_user(user: Optional[User], password: str):
    """Validates user and its password"""
    if not user:
        raise ex.USER_CREDENTIALS_ER

    salted_pwd = salt_password(password, user.salt)
    password_is_valid = verify_password(salted_pwd, user.password_hash)

    if password_is_valid:
        logger.info(f"Auth success for user '{user.id.id}'")
        return user
    else:
        logger.info(f"Auth failure for user '{user.id.id}'")
        raise ex.USER_CREDENTIALS_ER


def authenticate_by_email(
    email: str,
    password: str,
    bus: MessageBus,
) -> Optional[User]:
    logger.info(f"Trying to authenticate email '{email}'")
    user = views.credentials_email(email, bus)
    return check_user(user, password)


def authenticate_by_id(
    user_id: str,
    password: str,
    bus: MessageBus,
) -> Optional[User]:
    logger.info(f"Trying to authenticate user id '{user_id}'")
    user = views.credentials_id(user_id, bus)
    return check_user(user, password)


@router.post(s.API_TOKEN.path(), deprecated=True)
@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    bus: MessageBus = Depends(message_bus),
):
    """
    With credentials, creates new access and refresh tokens

    If you add scopes, it will get merged with current user
    roles.
    """
    if "@" not in form_data.username:
        raise ex.USER_CREDENTIALS_ER
    user = authenticate_by_email(form_data.username, form_data.password, bus)

    if user.is_pending_validation():
        raise ex.USER_PENDING_VALIDATION
    if user.is_disabled():
        raise ex.USER_INACTIVE

    scopes = user.roles
    if form_data.scopes:
        for requested_scope in form_data.scopes:
            if requested_scope not in user.roles:
                raise ex.AUTH_SCOPE_MISMATCH
    scopes = list(set(scopes).intersection(form_data.scopes))

    access_token = AccessToken(subject=user.id.id, scopes=scopes, fresh=True)
    # TODO not create a new refresh token if one already exists
    # Check https://docs.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens # noqa: E501
    refresh_token = RefreshToken(subject=user.id.id, scopes=scopes)

    return LoginResponse(
        user_id=user.id.id,
        access_token=access_token.to_token(),
        refresh_token=refresh_token.to_token(),
        access_token_expires=access_token.exp_time,
        refresh_token_expires=refresh_token.exp_time,
    )


@router.post("/refresh")
async def refresh_access_token(
    token: RefreshToken = Depends(get_refresh_token),
    bus: MessageBus = Depends(message_bus),
):
    """
    Refreshes token. This will generate a new access token however it will
    not be fresh since we don't validate user credentials.
    Can't be used for sensitive/administrative endpoints

    For accessing /refresh endpoint remember to **change access_token**
    *with refresh_token* in the header `Authorization: Bearer <refresh_token>`

    From RFC 6749 https://datatracker.ietf.org/doc/html/rfc6749#section-1.5

    ```
    +--------+                                           +---------------+
    |        |--(A)------- Authorization Grant --------->|               |
    |        |                                           |               |
    |        |<-(B)----------- Access Token -------------|               |
    |        |               & Refresh Token             |               |
    |        |                                           |               |
    |        |                            +----------+   |               |
    |        |--(C)---- Access Token ---->|          |   |               |
    |        |                            |          |   |               |
    |        |<-(D)- Protected Resource --| Resource |   | Authorization |
    | Client |                            |  Server  |   |     Server    |
    |        |--(E)---- Access Token ---->|          |   |               |
    |        |                            |          |   |               |
    |        |<-(F)- Invalid Token Error -|          |   |               |
    |        |                            +----------+   |               |
    |        |                                           |               |
    |        |--(G)----------- Refresh Token ----------->|               |
    |        |                                           |               |
    |        |<-(H)----------- Access Token -------------|               |
    +--------+           & Optional Refresh Token        +---------------+
    ```

     The flow illustrated includes the following steps:

    (A)  The client requests an access token by authenticating with the
         authorization server and presenting an authorization grant.

    (B)  The authorization server authenticates the client and validates
         the authorization grant, and if valid, issues an access token
         and a refresh token.

    (C)  The client makes a protected resource request to the resource
         server by presenting the access token.

    (D)  The resource server validates the access token, and if valid,
         serves the request.

    (E)  Steps (C) and (D) repeat until the access token expires.  If the
         client knows the access token expired, it skips to step (G);
         otherwise, it makes another protected resource request.

    (F)  Since the access token is invalid, the resource server returns
         an invalid token error.
    """
    user = views.by_id(token.subject, bus)

    scopes = list(set(token.scopes).intersection(set(user.roles)))
    access_token = AccessToken(subject=user.id.id, scopes=scopes, fresh=False)
    return {
        "access_token": access_token.to_token(),
        "access_token_expires": access_token.exp_time,
    }