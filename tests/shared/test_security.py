import io
from tempfile import TemporaryFile

import pytest
from cryptography.fernet import Fernet

from kpm.shared.security import *
from kpm.shared.security.aes256 import Aes256FileCypher
from kpm.shared.security.chacha20poly import ChaCha20PolyFileCypher


def test_salt():
    s = generate_salt()
    assert isinstance(s, str)


def test_salt_password():
    sp = salt_password("password,", "salt")
    assert isinstance(sp, str)
    assert sp.split(",")[0] == "password"
    assert sp.split(",")[1] == "salt"
    assert len(sp.split(",")) == 2


def test_hash():
    assert isinstance(hash_password("password"), str)
    assert len(hash_password("password")) == 60


def test_password_verify():
    assert verify_password(
        "password",
        "$2b$12$Hzgp1lAu1tA5O1Qizcjei.KXMhl9Z5.uejg5RePR9whnDuAqTbCQi",
    )


CIPHERS_TO_TEST = [
    Aes256FileCypher,
    ChaCha20PolyFileCypher,
    # StreamingAEADFileCypher
]


@pytest.mark.parametrize("Cipher_Cls", CIPHERS_TO_TEST)
class TestFileCyphers:
    def test_end_to_end(self, Cipher_Cls):
        # Key Encryption Key
        kek_bytes = Fernet.generate_key()
        kek = base64.b64encode(kek_bytes).decode("utf-8")
        data_key = Cipher_Cls.generate_data_key(kek)
        cipher = Cipher_Cls(data_key, kek)

        bytes_to_cipher = os.urandom(200)

        with io.BytesIO(
            bytes_to_cipher
        ) as plain, TemporaryFile() as enc, TemporaryFile() as deciphered_io:

            # Encrypting
            cipher.encrypt(plain, enc)
            # We have encrypted bytes
            enc.seek(0)
            assert enc.read() != bytes_to_cipher

            enc.seek(0)
            # Decrypting
            cipher.decrypt(enc, deciphered_io)

            deciphered_io.seek(0)
            assert deciphered_io.read() == bytes_to_cipher

    def test_wrong_kek_data_keygen(self, Cipher_Cls):
        kek_bytes = b"wrong kek init here"
        kek = base64.b64encode(kek_bytes).decode("utf-8")

        with pytest.raises(ValueError):
            data_key = Cipher_Cls.generate_data_key(kek)

    def test_wrong_kek_class_init(self, Cipher_Cls):
        kek_bytes = Fernet.generate_key()
        kek = base64.b64encode(kek_bytes).decode("utf-8")
        data_key = Cipher_Cls.generate_data_key(kek)

        cipher = Cipher_Cls(data_key, "wrong KEK")

        bytes_to_cipher = os.urandom(200)

        with io.BytesIO(bytes_to_cipher) as plain, io.BytesIO() as enc:
            with pytest.raises(ValueError):
                cipher.encrypt(plain, enc)

    def test_wrong_decrypt_key(self, Cipher_Cls):
        # Key Encryption Key
        kek_bytes = Fernet.generate_key()
        kek = base64.b64encode(kek_bytes).decode("utf-8")
        data_key = Cipher_Cls.generate_data_key(kek)
        cipher = Cipher_Cls(data_key, kek)

        bytes_to_cipher = os.urandom(200)

        with io.BytesIO(
            bytes_to_cipher
        ) as plain, io.BytesIO() as enc, io.BytesIO() as deciphered_io:
            cipher.encrypt(plain, enc)
            enc.seek(0)

            wrong_data_key = Cipher_Cls.generate_data_key(kek)
            wrong_cipher = Cipher_Cls(wrong_data_key, kek)
            # Decrypting
            with pytest.raises(ValueError):
                wrong_cipher.decrypt(enc, deciphered_io)

    def test_corrupted_file(self, Cipher_Cls):
        # Key Encryption Key
        kek_bytes = Fernet.generate_key()
        kek = base64.b64encode(kek_bytes).decode("utf-8")
        data_key = Cipher_Cls.generate_data_key(kek)
        cipher = Cipher_Cls(data_key, kek)

        corrypted_enc_bytes = os.urandom(200)

        with io.BytesIO(
            corrypted_enc_bytes
        ) as corrupted, io.BytesIO() as deciphered_io:

            # Decrypting
            with pytest.raises(ValueError):
                cipher.decrypt(corrupted, deciphered_io)
