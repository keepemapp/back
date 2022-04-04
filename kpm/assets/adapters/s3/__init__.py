from io import BytesIO
from tempfile import SpooledTemporaryFile, TemporaryFile

import boto3
from botocore.exceptions import ClientError

from kpm.assets.domain.repositories import EncryptedAssetFileRepository
from kpm.settings import settings as s
from kpm.shared.log import logger


class AssetFileS3Repository(EncryptedAssetFileRepository):
    """

    Future improvement: move to async with aiobotocore
    """

    def __init__(
        self,
        url: str = s.ASSET_S3_URL,
        access_key: str = s.ASSET_S3_ACCESS,
        secret_key: str = s.ASSET_S3_SECRET,
        bucket: str = s.ASSET_S3_BUCKET,
    ):
        self._client = boto3.client(
            "s3",
            endpoint_url=url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._bucket = bucket

    def _create(self, location: str, file: BytesIO):
        location = location.replace("\\", "/")
        try:
            file.seek(0)
            logger.debug(
                f"Saving file to bucket '{self._bucket}/{location}'",
                component="s3",
            )
            resp = self._client.put_object(
                Body=file, Bucket=self._bucket, Key=location
            )
            file.close()
            status = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status // 100 != 2:
                logger.error(
                    f"Cannot add s3 file '{location}': {resp}", component="s3"
                )
                raise RuntimeError("File could not be saved. Try later")
        except ClientError as e:
            logger.error(
                f"Cannot add s3 file '{location}'. Error '{e}'", component="s3"
            )
            raise RuntimeError(f"Could not put file. Error '{e}'")

        logger.info(f"Added file '{location}'")

    def _get(self, location: str) -> TemporaryFile:
        location = location.replace("\\", "/")
        try:
            file = SpooledTemporaryFile()
            self._client.download_fileobj(
                Bucket=self._bucket, Key=location, Fileobj=file
            )
            logger.debug(
                f"File '{location}' downloaded from s3", component="s3"
            )
            return file
        except ClientError as e:
            logger.error(
                f"Cannot access s3 file '{location}'. Error {e}",
                component="s3",
            )
            raise RuntimeError("Could not get file")
        except ValueError as e:
            logger.error(
                f"Cannot decrypt s3 file '{location}'. Error {e}",
                component="s3",
            )
            raise e

    def delete(self, location: str):
        location = location.replace("\\", "/")
        resp = self._client.delete_object(Bucket=self._bucket, Key=location)
        status = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status // 100 != 2:
            logger.error(
                f"Cannot delete s3 file '{location}': {resp}", component="s3"
            )
            raise RuntimeError("Could not delete file")
        logger.info(f"Removed file '{location}'", component="s3")
