from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status

from emo.settings import settings
from emo.settings import settings as cfg
from emo.shared.domain.usecase import EventPublisher
from emo.shared.infra.fastapi.schemas import TokenData
from emo.shared.infra.memrepo.message_bus import NoneEventPub


def event_bus() -> EventPublisher:
    yield NoneEventPub()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.API_V1.concat(settings.API_TOKEN).prefix
)


async def get_authorized_token(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, cfg.SECRET_KEY, algorithms=[cfg.ALGORITHM])
        token_data = TokenData(**payload)
        if not token_data.user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return token_data


async def get_active_user_token(
    token: TokenData = Depends(get_authorized_token),
) -> TokenData:
    inactive_user_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Operation forbidden for inactive users",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token.disabled:
        raise inactive_user_exception
    return token
