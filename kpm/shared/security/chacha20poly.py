import base64
import time
from typing import BinaryIO

from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes
from cryptography.fernet import Fernet

from kpm.shared.log import logger
from kpm.shared.security import FileCypher


class ChaCha20PolyFileCypher(FileCypher):
    BLOCK_SIZE = 512 * 1024  # 1024 * 1024  # 1MB at most
    NONCE_SIZE = 12

    def __init__(self, data_key: str, key_encryption_key: str):
        """Class to encrypt and decrypt files using ChaCha20-Poly1350

        ```
        import io
        import base64
        from Crypto.Random import get_random_bytes
        from kpm.shared.security import ChaCha20PolyFileCypher

        # Obtain Keys
        kekb = get_random_bytes(32)
        kek = base64.b64encode(kekb).decode('utf-8')
        data_key = ChaCha20PolyFileCypher.generate_data_key(kek)

        cipher = ChaCha20PolyFileCypher(data_key, kek)

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

        **WARNING**: In a AMD 5959X it costs to encrypt and decrypt a file of:
        * 32MB  e: 0.13s  d: 0.13s (b'0' * 2 ** 25)
        * 250MB e: 1.2s   d: 1.2s  (b'0' * 2 ** 28)
        * 1GB   e: 4.9s   d: 4.6   (b'0' * 2 ** 30)
        * 8GB   e: 39s    d: 38s   (b'0' * 2 ** 33)

        It can be slow for bigger files so we can investigate faster ones in
        the future. As of now seems good enough.

        :param data_key: Encrypted data encryption key
        :param key_encryption_key: Key to decypher the data key
        """
        self.__dek = data_key
        self.__kek = key_encryption_key

    def encrypt(self, plain_io: BinaryIO, cypher_io: BinaryIO):
        # It is slow
        # Recover data encryption Key
        dekb = self.__get_data_key()
        start_time = time.time()
        # Encrypt file
        # It is slow
        self._encrypt(dekb, plain_io, cypher_io)
        logger.debug("Encryption time %s seconds" % (time.time() - start_time))

    def decrypt(self, cypher_io: BinaryIO, plain_io: BinaryIO):
        # Recover data encryption Key
        dekb = self.__get_data_key()

        # Decipher file
        # It is slow
        start_time = time.time()
        self._decrypt(dekb, cypher_io, plain_io)
        logger.debug("Decryption time %s seconds" % (time.time() - start_time))

    @staticmethod
    def __get_cypher(key, nonce=None):
        if not nonce:
            nonce = get_random_bytes(ChaCha20PolyFileCypher.NONCE_SIZE)
        return ChaCha20_Poly1305.new(key=key, nonce=nonce)

    @staticmethod
    def _encrypt(keyb: bytes, inf: BinaryIO, outf: BinaryIO):
        inf.seek(0)
        cipher = ChaCha20PolyFileCypher.__get_cypher(keyb)
        nonce = cipher.nonce
        outf.write(nonce)
        outf.seek(16, 1)  # go forward of 16 bytes, placeholder for digest tag

        for block in ChaCha20PolyFileCypher._read_as_blocks(inf):
            outf.write(cipher.encrypt(block))

        outf.seek(
            ChaCha20PolyFileCypher.NONCE_SIZE
        )  # Write at allocated space
        outf.write(cipher.digest())  # Write digest tag

    @staticmethod
    def _decrypt(keyb: bytes, encrypted: BinaryIO, plain: BinaryIO):
        """

        :param encrypted:
        :param plain:
        :raises: ValueError – if the MAC does not match.
          The message has been tampered with or the key is incorrect.
        """
        encrypted.seek(0)
        plain.seek(0)

        nonce = encrypted.read(12)
        digest = encrypted.read(16)

        cipher = ChaCha20PolyFileCypher.__get_cypher(keyb, nonce=nonce)
        for block in ChaCha20PolyFileCypher._read_as_blocks(encrypted):
            plain.write(cipher.decrypt(block))
        cipher.verify(digest)

    @staticmethod
    def _read_as_blocks(file: BinaryIO):
        """Generator function to read from a file BLOCK_SIZE bytes."""
        while True:
            data = file.read(ChaCha20PolyFileCypher.BLOCK_SIZE)
            # If file was opened in rawIO, EOF is only reached
            # when b'' is returned.
            # pylint: disable=g-explicit-bool-comparison
            if data == b"":
                break
            # pylint: enable=g-explicit-bool-comparison
            yield data

    def __get_data_key(self) -> bytes:
        kek_bytes = base64.b64decode(self.__kek)
        f = Fernet(kek_bytes)
        plain = f.decrypt(base64.b64decode(self.__dek))
        return plain

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
        from Crypto.Random import get_random_bytes
        kek_bytes = get_random_bytes(32)
        kek = base64.b64encode(kek_bytes).decode('utf-8')
        print("Keep this safe", kek)
        ```
        """
        data_key = get_random_bytes(32)
        kek_bytes = base64.b64decode(kek)
        dekb = ChaCha20PolyFileCypher._encrypt_data_key(kek_bytes, data_key)
        return base64.b64encode(dekb).decode("utf-8")
