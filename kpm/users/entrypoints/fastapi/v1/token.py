from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import (
    AccessToken,
    RefreshToken,
    from_token,
)
from kpm.shared.entrypoints.fastapi.dependencies import message_bus, user_view
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_refresh_token
from kpm.shared.log import logger
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.domain import commands as cmds
from kpm.users.domain.model import (
    InvalidScope,
    InvalidSession,
    MissmatchPasswordException,
    User,
    UserNotFound,
    ValidationPending,
)
from kpm.users.entrypoints.fastapi.v1.schemas.token import LoginResponse

router = APIRouter(
    responses={404: {"description": "Not found"}}, tags=["auth"]
)


@router.post(s.API_TOKEN.path(), deprecated=True)
@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    bus: MessageBus = Depends(message_bus),
    views=Depends(user_view),
):
    """
    With credentials, creates new access and refresh tokens

    If you add scopes, it will get merged with current user
    roles.
    """
    try:
        cmd = cmds.LoginUser(
            email=form_data.username,
            password=form_data.password,
            device_id=form_data.client_id,
            scopes=form_data.scopes,
        )
        bus.handle(cmd)
        raw_token = views.get_active_refresh_token(bus, session_id=cmd.id)
        refresh_token = from_token(raw_token)
        access_token = AccessToken(
            subject=refresh_token.subject,
            scopes=refresh_token.scopes,
            fresh=True,
        )

        return LoginResponse(
            user_id=refresh_token.subject,
            access_token=access_token.to_token(),
            refresh_token=raw_token,
            access_token_expires=access_token.exp_time,
            refresh_token_expires=refresh_token.exp_time,
        )
    except ValidationPending:
        raise ex.USER_PENDING_VALIDATION
    except (UserNotFound, InvalidSession, MissmatchPasswordException):
        raise ex.USER_CREDENTIALS_ER
    except InvalidScope:
        raise ex.AUTH_SCOPE_MISMATCH
    except Exception as e:
        raise e


@router.delete("/logout")
async def refresh_access_token(
    token: RefreshToken = Depends(get_refresh_token),
    bus: MessageBus = Depends(message_bus),
):
    """
    Invalidates server-side the token
    """
    raw, token = token
    cmd = cmds.RemoveSession(token=raw, removed_by=token.subject)
    bus.handle(cmd)


@router.post("/refresh")
async def refresh_access_token(
    token: RefreshToken = Depends(get_refresh_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(user_view),
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
    try:
        raw, token = token
        views.get_active_refresh_token(bus, token=raw)
        access_token = AccessToken(
            subject=token.subject, scopes=token.scopes, fresh=False
        )
    except InvalidSession:
        bus.handle(cmds.RemoveSession(token=raw, removed_by="backend"))
        raise ex.TOKEN_ER
    except Exception as e:
        raise e

    return {
        "access_token": access_token.to_token(),
        "access_token_expires": access_token.exp_time,
    }
