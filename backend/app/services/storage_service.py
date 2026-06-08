"""Storage service layer for S3/MinIO/Cloud Storage."""

import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Service layer for object storage operations."""

    def __init__(self, backend: str = "local"):
        self.backend = backend
        self._client = None

    async def get_client(self):
        """Get or create storage client."""
        if self._client is None:
            if self.backend == "s3":
                self._client = await self._create_s3_client()
            elif self.backend == "gcs":
                self._client = await self._create_gcs_client()
            else:
                self._client = None  # Local filesystem
        return self._client

    async def _create_s3_client(self):
        """Create S3 client."""
        try:
            import boto3
            from botocore.config import Config

            config = Config(
                signature_version="s3v4",
            )
            client = boto3.client(
                "s3",
                endpoint_url=None,  # Use default AWS endpoint
                config=config,
            )
            return client
        except ImportError:
            logger.warning("boto3 not installed, using local storage")
            return None

    async def _create_gcs_client(self):
        """Create Google Cloud Storage client."""
        try:
            from google.cloud import storage

            client = storage.Client()
            return client
        except ImportError:
            logger.warning("google-cloud-storage not installed, using local storage")
            return None

    async def upload_snapshot(
        self,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str = "text/html",
    ) -> str:
        """Upload a snapshot to storage."""
        client = await self.get_client()
        if not client:
            logger.warning("No storage client available, skipping upload")
            return ""

        if self.backend == "s3":
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        elif self.backend == "gcs":
            bucket_obj = client.bucket(bucket)
            blob = bucket_obj.blob(key)
            blob.upload_from_string(content, content_type=content_type)

        return f"{self.backend}://{bucket}/{key}"

    async def download_snapshot(self, url: str) -> bytes | None:
        """Download a snapshot from storage."""
        if not url.startswith(f"{self.backend}://"):
            return None

        parts = url.replace(f"{self.backend}://", "").split("/", 1)
        if len(parts) != 2:
            return None

        bucket, key = parts
        client = await self.get_client()
        if not client:
            return None

        try:
            if self.backend == "s3":
                response = client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()
            elif self.backend == "gcs":
                bucket_obj = client.bucket(bucket)
                blob = bucket_obj.blob(key)
                return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"Failed to download snapshot: {e}")
            return None

    async def delete_snapshot(self, bucket: str, key: str) -> bool:
        """Delete a snapshot from storage."""
        client = await self.get_client()
        if not client:
            return False

        try:
            if self.backend == "s3":
                client.delete_object(Bucket=bucket, Key=key)
            elif self.backend == "gcs":
                bucket_obj = client.bucket(bucket)
                bucket_obj.blob(key).delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return False
