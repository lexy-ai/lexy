from abc import ABC, abstractmethod


class StorageClient(ABC):
    """Abstract base class for storage clients."""

    @abstractmethod
    def is_authenticated(self) -> bool:
        pass

    @abstractmethod
    def list_buckets(self) -> list[str]:
        pass

    @abstractmethod
    def upload_object(self, fileobj, bucket_name: str, object_name: str, rewind: bool = True) -> dict:
        pass

    @abstractmethod
    def generate_presigned_url(self, bucket_name: str, object_name: str, expiration: int = 3600) -> str:
        pass

    @abstractmethod
    def delete_object(self, bucket_name: str, object_name: str) -> None:
        pass
