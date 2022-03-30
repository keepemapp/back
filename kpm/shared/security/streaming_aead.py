import io
from typing import BinaryIO

import tink
from tink import cleartext_keyset_handle, streaming_aead

from kpm.shared.security import FileCypher


class StreamingAEADFileCypher(FileCypher):
    BLOCK_SIZE = 1024 * 1024

    def read_as_blocks(self, file: BinaryIO):
        """Generator function to read from a file BLOCK_SIZE bytes.
        Args:
          file: The file object to read from.
        Yields:
          Returns up to BLOCK_SIZE bytes from the file.
        """
        while True:
            data = file.read(self.BLOCK_SIZE)
            # If file was opened in rawIO, EOF is only reached
            # when b'' is returned.
            # pylint: disable=g-explicit-bool-comparison
            if data == b"":
                break
            # pylint: enable=g-explicit-bool-comparison
            yield data

    def encrypt_file(
        self,
        input_file: BinaryIO,
        output_file: BinaryIO,
        associated_data: bytes,
        primitive: streaming_aead.StreamingAead,
    ):
        """Encrypts a file with the given streaming AEAD primitive.

        Args:
          input_file: File to read from.
          output_file: File to write to.
          associated_data: Associated data provided for the AEAD.
          primitive: The streaming AEAD primitive used for encryption.
        """
        tmp_file = io.BytesIO()
        input_file.seek(0)
        with open(
            "temp.enc", "wb+"
        ) as tmp_file, primitive.new_encrypting_stream(
            tmp_file, associated_data
        ) as enc_stream:
            for data_block in self.read_as_blocks(input_file):
                enc_stream.write(data_block)
            # FIXME Since closing the encrypting stream forces closure of file
            # we need a temporary one and iterate twice over the data
        with open("temp.enc", "rb") as tmp_file:
            print(
                tmp_file.seek(0, io.SEEK_END) / 1024 / 1024 / 1024,
                "GB (encripted)",
            )
            tmp_file.seek(0)
            for data_block in self.read_as_blocks(tmp_file):
                output_file.write(data_block)

    def decrypt_file(
        self,
        input_file: BinaryIO,
        output_file: BinaryIO,
        associated_data: bytes,
        primitive: streaming_aead.StreamingAead,
    ):
        """Decrypts a file with the given streaming AEAD primitive.

        This function will cause the program to exit with 1 if the
        decryption fails.

        Args:
          input_file: File to read from.
          output_file: File to write to.
          associated_data: Associated data provided for the AEAD.
          primitive: The streaming AEAD primitive used for decryption.
        """
        try:
            input_file.seek(0)
            with primitive.new_decrypting_stream(
                input_file, associated_data
            ) as dec_stream:
                for data_block in self.read_as_blocks(dec_stream):
                    output_file.write(data_block)
        except tink.TinkError as e:
            # logger.exception('Error decrypting ciphertext: %s', e)
            raise e

    @staticmethod
    def create_data_key() -> bytes:
        """Creates an AWS256 key to encrypt 1MB chunks of data
        Similar to https://developers.google.com/tink/generate-plaintext-keyset

        The key is a binary piece of data which json representation is:

        ```json
        {
          "primaryKeyId": 800000000,
          "key": [
            {
              "keyData": {
                "typeUrl": "type.g....com/....crypto.tink.AesGcmHkdfStrea...",
                "value": "ECfCCCCCc...",
                "keyMaterialType": "SYMMETRIC"
              },
              "status": "ENABLED",
              "keyId": 800000000,
              "outputPrefixType": "RAW"
            }
          ]
        }
        ```
        """
        streaming_aead.register()
        key_template = (
            streaming_aead.streaming_aead_key_templates.AES256_GCM_HKDF_1MB
        )
        keyset_handle = tink.KeysetHandle.generate_new(key_template)
        with io.BytesIO() as f:
            cleartext_keyset_handle.write(
                tink.BinaryKeysetWriter(f), keyset_handle
            )
            key = f.getvalue()
        return key

    def get_data_key_primitive(self, key: bytes):
        cipher = cleartext_keyset_handle.read(tink.BinaryKeysetReader(key))
        return cipher.primitive(streaming_aead.StreamingAead)
