import base64
import os
from abc import ABC, abstractmethod
from typing import BinaryIO

from passlib.context import CryptContext

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


class FileCypher(ABC):
    @abstractmethod
    def encrypt(self, plain_io: BinaryIO, cypher_io: BinaryIO):
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, cypher_io: BinaryIO, plain_io: BinaryIO):
        raise NotImplementedError

    @staticmethod
    def generate_data_key(kek: str):
        raise NotImplementedError
