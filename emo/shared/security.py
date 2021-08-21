from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import base64

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_salt():
    rand = os.urandom(8)
    return str(base64.b64encode(rand))


def salt_password(password: str, salt: str) -> str:
    return password + salt


def verify_password(salted_password, hashed_password):
    return pwd_context.verify(salted_password, hashed_password)


def hash_password(salted_password):
    return pwd_context.hash(salted_password)
