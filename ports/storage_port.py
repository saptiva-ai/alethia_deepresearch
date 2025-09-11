from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional


class StorageMetadata:
    """Metadata for stored objects."""
    def __init__(self, key: str, size: int, modified: datetime, content_type: str = "", etag: str = ""):
        self.key = key
        self.size = size
        self.modified = modified
        self.content_type = content_type
        self.etag = etag

class StoragePort(ABC):
    """Port for object storage operations (MinIO/S3/FS)."""

    @abstractmethod
    def store_object(self, key: str, data: bytes, metadata: Optional[dict[str, str]] = None) -> bool:
        """
        Store an object.

        Args:
            key: Object key/path
            data: Object data as bytes
            metadata: Optional metadata dict

        Returns:
            True if stored successfully, False otherwise
        """
        pass

    @abstractmethod
    def store_file(self, key: str, file_path: Path, metadata: Optional[dict[str, str]] = None) -> bool:
        """
        Store a file.

        Args:
            key: Object key/path
            file_path: Path to the file to store
            metadata: Optional metadata dict

        Returns:
            True if stored successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_object(self, key: str) -> Optional[bytes]:
        """
        Retrieve an object.

        Args:
            key: Object key/path

        Returns:
            Object data as bytes or None if not found
        """
        pass

    @abstractmethod
    def get_object_stream(self, key: str) -> Optional[BinaryIO]:
        """
        Get an object as a stream.

        Args:
            key: Object key/path

        Returns:
            Binary stream or None if not found
        """
        pass

    @abstractmethod
    def delete_object(self, key: str) -> bool:
        """
        Delete an object.

        Args:
            key: Object key/path

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if an object exists.

        Args:
            key: Object key/path

        Returns:
            True if object exists, False otherwise
        """
        pass

    @abstractmethod
    def list_objects(self, prefix: str = "", limit: int = 1000) -> list[StorageMetadata]:
        """
        List objects with optional prefix filter.

        Args:
            prefix: Optional prefix to filter by
            limit: Maximum number of objects to return

        Returns:
            List of StorageMetadata objects
        """
        pass

    @abstractmethod
    def get_metadata(self, key: str) -> Optional[StorageMetadata]:
        """
        Get object metadata.

        Args:
            key: Object key/path

        Returns:
            StorageMetadata object or None if not found
        """
        pass

    @abstractmethod
    def create_presigned_url(self, key: str, expiry_seconds: int = 3600, method: str = "GET") -> Optional[str]:
        """
        Create a presigned URL for object access.

        Args:
            key: Object key/path
            expiry_seconds: URL expiry time in seconds
            method: HTTP method (GET, PUT, etc.)

        Returns:
            Presigned URL or None if operation fails
        """
        pass

    @abstractmethod
    def copy_object(self, source_key: str, dest_key: str) -> bool:
        """
        Copy an object to a new key.

        Args:
            source_key: Source object key
            dest_key: Destination object key

        Returns:
            True if copied successfully, False otherwise
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the storage service is available and healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass
