from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, Params, paginate

from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi import query_params
from kpm.shared.entrypoints.fastapi.dependencies import message_bus, user_view
from kpm.shared.entrypoints.fastapi.exceptions import FORBIDDEN_GENERIC
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.domain import commands as cmds
from kpm.users.domain.model import KeepActionError, KeepAlreadyDeclined
from kpm.users.entrypoints.fastapi.v1.schemas import keeps as schemas
from kpm.users.entrypoints.fastapi.v1.schemas.users import UserPublic

router = APIRouter(
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
    **s.API_KEEP_PATH.dict(),
)


@router.get(
    "", responses={status.HTTP_200_OK: {"model": Page[schemas.KeepResponse]}}
)
async def list_keeps(
    order_by: str = query_params.order_by,
    order: str = query_params.order,
    state: str = query_params.state,
    paginate_params: Params = Depends(),
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(user_view),
):
    keeps_raw = views.user_keeps(bus, token.subject, order_by, order, state)
    users = set([k["requester"] for k in keeps_raw] + [k["requested"] for k in keeps_raw])
    user_lookup = {u["id"]: u for u in views.users_public_info(list(users), bus)}

    keeps = list()
    for k in keeps_raw:
        k["requester"] = UserPublic(**user_lookup[k.pop("requester")])
        k["requested"] = UserPublic(**user_lookup[k.pop("requested")])
        keeps.append(schemas.KeepResponse(**k))

    return paginate(keeps, paginate_params)


@router.post("", status_code=status.HTTP_201_CREATED)
async def new_keep(
    request: schemas.RequestKeep,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(user_view),
):
    found_value = None
    if request.to_id:
        found_value = views.by_id(request.to_id, bus)
        user_id = request.to_id
    elif request.to_code:
        found_value = user_id = views.id_from_referral(request.to_code, bus)
    elif request.to_email:
        found_value = user_id = views.id_from_email(request.to_email, bus)
    if not found_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested user does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    cmd = cmds.RequestKeep(requester=token.subject, requested=user_id)
    bus.handle(cmd)


@router.put("/accept", status_code=status.HTTP_204_NO_CONTENT)
async def accept_keep(
    request: schemas.AcceptKeep,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    """Accepts the keep request"""
    cmd = cmds.AcceptKeep(by=token.subject, keep_id=request.keep_id)
    try:
        bus.handle(cmd)
    except KeepActionError:
        raise FORBIDDEN_GENERIC
    except Exception as e:
        raise e


@router.put("/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline_keep(
    request: schemas.DeclineKeep,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    """Decline a keep. Can be a pending request or one already accepted."""
    cmd = cmds.DeclineKeep(
        by=token.subject, keep_id=request.keep_id, reason=request.reason
    )
    try:
        bus.handle(cmd)
    except KeepActionError:
        raise FORBIDDEN_GENERIC
    except KeepAlreadyDeclined:
        pass
    except Exception as e:
        raise e
