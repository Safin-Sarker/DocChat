"""Storage service for handling file uploads (S3 or local)."""

import os
import shutil
from pathlib import Path
from typing import Optional
import uuid
from app.core.config import settings


class StorageService:
    """Service for storing uploaded files (S3 or local filesystem)."""

    def __init__(self):
        """Initialize storage service."""
        self.use_local = settings.USE_LOCAL_STORAGE

        if self.use_local:
            # Create local storage directory if it doesn't exist
            self.storage_path = Path(settings.LOCAL_STORAGE_PATH)
            self.storage_path.mkdir(parents=True, exist_ok=True)
            print(f"Using local storage at: {self.storage_path}")
        else:
            # Initialize S3 client
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                self.bucket_name = settings.AWS_BUCKET_NAME
                print(f"Using AWS S3 storage: {self.bucket_name}")
            except Exception as e:
                print(f"Error initializing S3 client: {e}")
                raise

    async def upload_file(
        self,
        file_path: str,
        filename: str,
        doc_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Upload file to storage.

        Args:
            file_path: Path to file to upload
            filename: Original filename
            doc_id: Document ID (optional, will generate if not provided)
            user_id: User ID for multi-tenant isolation

        Returns:
            Storage key/path for the uploaded file
        """
        if not doc_id:
            doc_id = str(uuid.uuid4())

        # Create unique storage key with user isolation
        if user_id:
            storage_key = f"{user_id}/{doc_id}/{filename}"
        else:
            storage_key = f"{doc_id}/{filename}"

        if self.use_local:
            return await self._upload_local(file_path, storage_key)
        else:
            return await self._upload_s3(file_path, storage_key)

    async def _upload_local(self, file_path: str, storage_key: str) -> str:
        """Upload file to local storage.

        Args:
            file_path: Path to file
            storage_key: Storage key/path

        Returns:
            Local file path
        """
        try:
            # Create subdirectory for document
            dest_dir = self.storage_path / Path(storage_key).parent
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Copy file
            dest_path = self.storage_path / storage_key
            shutil.copy2(file_path, dest_path)

            print(f"File uploaded to local storage: {dest_path}")
            return str(dest_path)

        except Exception as e:
            print(f"Error uploading to local storage: {e}")
            raise

    async def _upload_s3(self, file_path: str, storage_key: str) -> str:
        """Upload file to S3.

        Args:
            file_path: Path to file
            storage_key: S3 key

        Returns:
            S3 URL
        """
        try:
            # Upload to S3
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                storage_key
            )

            # Generate S3 URL
            s3_url = f"s3://{self.bucket_name}/{storage_key}"
            print(f"File uploaded to S3: {s3_url}")

            return s3_url

        except Exception as e:
            print(f"Error uploading to S3: {e}")
            raise

    async def upload_image(
        self,
        image_data: bytes,
        doc_id: str,
        image_id: str,
        extension: str = "png",
        user_id: Optional[str] = None
    ) -> str:
        """Upload image data to storage.

        Args:
            image_data: Image bytes
            doc_id: Document ID
            image_id: Image ID
            extension: File extension
            user_id: User ID for multi-tenant isolation

        Returns:
            Storage URL/path
        """
        if user_id:
            storage_key = f"{user_id}/{doc_id}/images/{image_id}.{extension}"
        else:
            storage_key = f"{doc_id}/images/{image_id}.{extension}"

        if self.use_local:
            return await self._upload_image_local(image_data, storage_key)
        else:
            return await self._upload_image_s3(image_data, storage_key)

    async def _upload_image_local(self, image_data: bytes, storage_key: str) -> str:
        """Upload image to local storage.

        Args:
            image_data: Image bytes
            storage_key: Storage key

        Returns:
            Local file path
        """
        try:
            # Create directory
            dest_dir = self.storage_path / Path(storage_key).parent
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Write image
            dest_path = self.storage_path / storage_key
            with open(dest_path, 'wb') as f:
                f.write(image_data)

            return str(dest_path)

        except Exception as e:
            print(f"Error uploading image to local storage: {e}")
            raise

    async def _upload_image_s3(self, image_data: bytes, storage_key: str) -> str:
        """Upload image to S3.

        Args:
            image_data: Image bytes
            storage_key: S3 key

        Returns:
            S3 URL
        """
        try:
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=image_data
            )

            return f"s3://{self.bucket_name}/{storage_key}"

        except Exception as e:
            print(f"Error uploading image to S3: {e}")
            raise

    async def delete_document_files(self, doc_id: str, user_id: Optional[str] = None):
        """Delete all files for a document.

        Args:
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation
        """
        if self.use_local:
            await self._delete_local(doc_id, user_id)
        else:
            await self._delete_s3(doc_id, user_id)

    async def _delete_local(self, doc_id: str, user_id: Optional[str] = None):
        """Delete local files for document.

        Args:
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation
        """
        try:
            if user_id:
                doc_dir = self.storage_path / user_id / doc_id
            else:
                doc_dir = self.storage_path / doc_id

            if doc_dir.exists():
                shutil.rmtree(doc_dir)
                print(f"Deleted local files for document: {doc_id}" + (f" (user: {user_id})" if user_id else ""))
        except Exception as e:
            print(f"Error deleting local files: {e}")
            raise

    async def _delete_s3(self, doc_id: str, user_id: Optional[str] = None):
        """Delete S3 files for document.

        Args:
            doc_id: Document ID
            user_id: User ID for multi-tenant isolation
        """
        try:
            # Build prefix with user isolation
            if user_id:
                prefix = f"{user_id}/{doc_id}/"
            else:
                prefix = f"{doc_id}/"

            # List and delete all objects with prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects}
                )
                print(f"Deleted S3 files for document: {doc_id}" + (f" (user: {user_id})" if user_id else ""))

        except Exception as e:
            print(f"Error deleting S3 files: {e}")
            raise

    def get_file_url(self, storage_key: str) -> str:
        """Get URL for a stored file.

        Args:
            storage_key: Storage key/path

        Returns:
            File URL
        """
        if self.use_local:
            return f"file://{self.storage_path / storage_key}"
        else:
            return f"s3://{self.bucket_name}/{storage_key}"
