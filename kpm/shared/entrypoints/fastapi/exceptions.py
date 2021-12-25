from fastapi import HTTPException, status

UNAUTHORIZED_GENERIC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorized to access this resource",
    headers={"WWW-Authenticate": "Bearer"},
)

USER_CREDENTIALS_ER = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
)

TOKEN_ER = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

AUTH_SCOPE_MISMATCH = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Incorrect auth scope",
)

FORBIDDEN_GENERIC = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You do not have access this resource",
    headers={"WWW-Authenticate": "Bearer"},
)

USER_INACTIVE = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User is not active.",
)

USER_PENDING_VALIDATION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="User not validated.",
)

NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found",
)
