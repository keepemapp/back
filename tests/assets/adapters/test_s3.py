import io
import os

import boto3
import botocore
import pytest
from botocore.exceptions import ClientError

from kpm.assets.adapters.s3 import AssetFileS3Repository
from kpm.shared.security.chacha20poly import ChaCha20PolyFileCypher

from kpm.settings import settings as s


ACTIVE_CIPHERS = [
    ChaCha20PolyFileCypher
]


@pytest.mark.integration
@pytest.mark.parametrize("CipherCls", ACTIVE_CIPHERS)
class TestS3Repository:

    def test_put_and_recover_file(self, CipherCls):
        s3 = boto3.client("s3", endpoint_url=s.ASSET_S3_URL,
            aws_access_key_id=s.ASSET_S3_ACCESS,
            aws_secret_access_key=s.ASSET_S3_SECRET,
        )
        enc_key = CipherCls.generate_data_key(s.DATA_KEY_ENCRYPTION_KEY)
        repo = AssetFileS3Repository()
        file_key = "test/file.test"
        bytes_to_cipher = os.urandom(20)

        # Upload
        with io.BytesIO(bytes_to_cipher) as plain:
            repo.create(file_key, file=plain, encryption_key=enc_key,
                        encryption_type=CipherCls.__name__)
        assert s3.get_object(Bucket=s.ASSET_S3_BUCKET, Key=file_key)

        # Download
        result_file = repo.get(file_key, encryption_key=enc_key,
                               encryption_type=CipherCls.__name__)
        result_bytes = result_file.read()
        result_file.close()
        assert result_bytes == bytes_to_cipher

        # Delete
        repo.delete(file_key)

        with pytest.raises(ClientError):
            s3.get_object(Bucket=s.ASSET_S3_BUCKET, Key=file_key)