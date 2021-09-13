from fastapi import HTTPException, status

UNAUTHORIZED_GENERIC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorized to access this resource",
    headers={"WWW-Authenticate": "Bearer"},
)
