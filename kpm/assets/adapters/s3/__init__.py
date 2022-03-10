from tempfile import TemporaryFile
import boto3
from botocore.exceptions import ClientError

from kpm.assets.domain.repositories import AssetFileRepository
from kpm.settings import settings as s
from kpm.shared.log import logger


class AssetFileS3Repository(AssetFileRepository):
    def __init__(self, url: str = s.ASSET_S3_URL,
                 access_key: str = s.ASSET_S3_ACCESS,
                 secret_key: str = s.ASSET_S3_SECRET,
                 bucket: str = s.ASSET_S3_BUCKET):
        self._client = boto3.client(
            "s3",
            endpoint_url=url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        self._bucket = bucket

    def create(self, location: str, file: TemporaryFile):
        resp = self._client.put_object(
            Body=file,
            Bucket=self._bucket,
            Key=location
        )
        file.close()
        status = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status // 100 != 2:
            logger.error(f"Cannot add s3 file '{location}': {resp}")
            raise RuntimeError("File could not be saved. Try later")
        logger.info(f"Added file '{location}'")

    def get(self, location: str) -> TemporaryFile:
        try:
            file = TemporaryFile()
            self._client.download_fileobj(Bucket=self._bucket, Key=location, Fileobj=file)
            file.seek(0)
        except ClientError as e:
            logger.error(f"Cannot access s3 file '{location}'. Error {e}")
            raise RuntimeError("Could not get file")
        return file

    def delete(self, location: str):
        resp = self._client.delete_object(Bucket=self._bucket, Key=location)
        status = resp.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status // 100 != 2:
            logger.error(f"Cannot delete s3 file '{location}': {resp}")
            raise RuntimeError("Could not delete file")
        logger.info(f"Removed file '{location}'")