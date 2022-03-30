import base64
import io
import os
import time
from typing import BinaryIO

import pyAesCrypt
from cryptography.fernet import Fernet

from kpm.shared.log import logger
from kpm.shared.security import FileCypher


class Aes256FileCypher(FileCypher):
    BLOCK_SIZE = 16 * 1024

    def __init__(self, data_key: str, key_encryption_key: str):
        """Encrypts file-like objects using AES 256
        ```
        import io
        import os
        import base64
        from cryptography.fernet import Fernet
        from kpm.shared.security.aes256 import Aes256FileCypher

        # Obtain Keys
        kek_bytes = Fernet.generate_key()
        kek = base64.b64encode(kek_bytes).decode("utf-8")
        data_key = Aes256FileCypher.generate_data_key(kek)

        cipher = Aes256FileCypher(data_key, kek)

        # Encrypting
        plain = io.BytesIO(b'This is a plain text')
        plain = io.BytesIO(b'0' * 2 ** 30)
        # print(plain.seek(0, io.SEEK_END)/1024/1024/1024, "GB")
        enc = io.BytesIO()
        cipher.encrypt(plain, enc)
        # encrypted_value = enc.getvalue()
        # print(encrypted_value)

        # Decrypting
        deciphered_io = io.BytesIO()
        cipher.decrypt(enc, deciphered_io)

        # result = deciphered_io.getvalue()
        # print(result == plain.getvalue())
        ```


        :param data_key:
        :param key_encryption_key:
        """
        self.__dek = data_key
        self.__kek = key_encryption_key

    def encrypt(self, plain_io: BinaryIO, cypher_io: BinaryIO):
        """Encrypts a file with a given key"""
        dekb = self.__get_data_key()

        plain_io.seek(0)
        start_time = time.time()
        pyAesCrypt.encryptStream(
            plain_io, cypher_io, dekb, Aes256FileCypher.BLOCK_SIZE
        )
        logger.debug("Encryption time %s seconds" % (time.time() - start_time))

    def decrypt(self, cypher_io: BinaryIO, plain_io: BinaryIO):
        """Decrypts a file with a given key"""
        dekb = self.__get_data_key()
        file_size = cypher_io.seek(0, io.SEEK_END)  # Not really efficient
        cypher_io.seek(0)
        start_time = time.time()
        pyAesCrypt.decryptStream(
            cypher_io, plain_io, dekb, Aes256FileCypher.BLOCK_SIZE, file_size
        )
        logger.debug("Decryption time %s seconds" % (time.time() - start_time))

    def __get_data_key(self) -> str:
        kek_bytes = base64.b64decode(self.__kek)
        f = Fernet(kek_bytes)
        plain = f.decrypt(base64.b64decode(self.__dek))
        return base64.b64encode(plain).decode("utf-8")

    @staticmethod
    def _encrypt_data_key(kekb: bytes, dekb: bytes):
        f = Fernet(kekb)
        token = f.encrypt(dekb)
        return token

    @staticmethod
    def generate_data_key(kek: str):
        """Generates a data encryption key and returns it cyphered with the
        key to encrypts the keys (kek).

        If you don't have a KEK, and it's the FIRST TIME you have some data,
        use
        ```
        import base64
        import os
        from cryptography.fernet import Fernet
        kek_bytes = Fernet.generate_key()
        kek = base64.b64encode(kek_bytes).decode('utf-8')
        print("Keep this safe", kek)
        ```
        """
        data_key = os.urandom(32)
        kek_bytes = base64.b64decode(kek)
        dekb = Aes256FileCypher._encrypt_data_key(kek_bytes, data_key)
        return base64.b64encode(dekb).decode("utf-8")
