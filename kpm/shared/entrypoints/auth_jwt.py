import uuid
from dataclasses import field
from datetime import timedelta
from typing import List, Optional, Union

from jose import jwt
from pydantic.dataclasses import dataclass

from kpm.settings import settings as s
from kpm.shared.domain.time_utils import now_utc_sec


def _get_expire_time(
    valid_from: int, expire_delta: Union[timedelta, int]
) -> Optional[int]:
    if not isinstance(valid_from, int):
        raise TypeError("Valid from must be an `int`.")
    if not expire_delta or expire_delta == 0:
        return None
    if isinstance(expire_delta, timedelta):
        return valid_from + int(expire_delta.total_seconds())
    elif isinstance(expire_delta, int):
        return valid_from + expire_delta
    else:
        raise TypeError(
            "Expire time has to be of type `Union[timedelta, int]` and "
            + f"it is if type `{type(expire_delta)}`"
        )


class JWTClaims:
    """
    Standard claim names from https://www.iana.org/assignments/jwt/jwt.xhtml
    """

    ISSUER: str = "iss"
    SUBJECT: str = "sub"
    AUDIENCE: str = "aud"
    JWT_ID: str = "jti"
    NOT_BEFORE: str = "nbf"
    EXPIRATION_TIME: str = "exp"
    ISSUED_AT: str = "iat"
    SCOPES: str = "scope"
    # Custom claims
    FRESH: str = "fsh"
    TYPE: str = "typ"


@dataclass
class JWTToken:
    """Data inside the token.

    It needs to be enough for all microservices so they do not need to ask
    for extra user information. Include auth groups, ids...
    """

    """Identifier for who this token is for example user_id"""
    subject: str
    """Indicate token is access_token or refresh_token"""
    type: str
    """Duration of the token"""
    exp_time_delta: Optional[Union[timedelta, int]] = None
    """Freshness of the access token for elevated privilege tasks"""
    fresh: bool = True
    """User access privileges this token has. For example `admin`"""
    scopes: List[str] = field(default_factory=list)
    """If values are obtained from another token, do not allow to transform
    back."""

    jwt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    exp_time: int = None
    not_before: int = field(default_factory=now_utc_sec)
    issued_at: int = field(default_factory=now_utc_sec)
    can_generate_str: bool = True

    def __post_init__(self):
        if not self.subject or not isinstance(self.subject, str):
            raise ValueError("Subject is needed.")
        if self.type not in ("access", "refresh"):
            raise ValueError("Token can only be of types access or refresh.")
        if not self.exp_time:
            self.exp_time = _get_expire_time(
                self.not_before, self.exp_time_delta
            )
        # We remove duplicate values
        self.scopes = list(set(self.scopes))

    def is_fresh(self) -> bool:
        return self.fresh

    def is_access(self) -> bool:
        return self.type == "access"

    def is_refresh(self) -> bool:
        return self.type == "refresh"

    def is_valid(self, scope: str = None) -> bool:
        """Checks if token validity conditions are met"""
        current_time = now_utc_sec()
        time_is_valid = self.not_before <= current_time < self.exp_time
        scope_is_valid = scope in self.scopes if scope else True

        return self.subject and time_is_valid and scope_is_valid

    def to_token(self) -> str:
        if not self.can_generate_str:
            raise ValueError("This token cannot be recreated")
        to_enc = {
            # Reserved claims
            JWTClaims.SUBJECT: self.subject,
            # "aud": None,
            JWTClaims.JWT_ID: self.jwt_id,
            JWTClaims.ISSUED_AT: self.issued_at,
            JWTClaims.NOT_BEFORE: self.not_before,
            # Custom claims
            JWTClaims.SCOPES: self.scopes,
            JWTClaims.TYPE: self.type,
        }

        if self.exp_time:
            to_enc[JWTClaims.EXPIRATION_TIME] = self.exp_time
        if isinstance(self.fresh, bool) and self.is_access():
            to_enc[JWTClaims.FRESH] = self.fresh

        return jwt.encode(
            claims=to_enc,
            key=s.JWT_SECRET_KEY,
            algorithm=s.JWT_ALGORITHM,
        )


@dataclass
class AccessToken(JWTToken):
    type: str = "access"
    exp_time_delta: Union[timedelta, int, None] = field(
        default=s.JWT_ACCESS_EXPIRE_TIME
    )


@dataclass
class RefreshToken(JWTToken):
    type: str = "refresh"
    exp_time_delta: Union[timedelta, int, None] = field(
        default=s.JWT_REFRESH_EXPIRE_TIME
    )


def from_token(encoded_token: str) -> Union[AccessToken, RefreshToken]:
    decoded = jwt.decode(
        token=encoded_token,
        key=s.JWT_SECRET_KEY,
        algorithms=s.JWT_DECODE_ALGORITHMS,
    )
    tok_cls = JWTToken
    if decoded.get("typ") == "access":
        tok_cls = AccessToken
    elif decoded.get("typ") == "refresh":
        tok_cls = RefreshToken
    else:
        raise TypeError("Token type not supported")

    return tok_cls(
        subject=decoded.get(JWTClaims.SUBJECT),
        fresh=decoded.get(JWTClaims.FRESH, False),
        scopes=decoded.get(JWTClaims.SCOPES),
        exp_time_delta=None,
        can_generate_str=False,
        exp_time=decoded.get(JWTClaims.EXPIRATION_TIME),
        issued_at=decoded.get(JWTClaims.ISSUED_AT),
        not_before=decoded.get(JWTClaims.NOT_BEFORE),
        jwt_id=decoded.get(JWTClaims.JWT_ID),
    )
