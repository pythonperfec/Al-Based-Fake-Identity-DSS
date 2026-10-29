from typing import Protocol, runtime_checkable, Tuple, List, Dict, Any, Optional


@runtime_checkable
class IObjectStorage(Protocol):
    async def store(self, file_bytes: bytes, filename: str, content_type: str) -> Tuple[str, str]:
        """Store bytes and return (storage_key, sha256_hex)."""
        ...

    async def retrieve(self, storage_key: str) -> Tuple[bytes, str]:
        """Retrieve binary bytes and content_type by storage key."""
        ...

    async def delete(self, storage_key: str) -> None:
        """Delete stored object by key."""
        ...


@runtime_checkable
class IJobQueue(Protocol):
    async def enqueue(self, screening_id: str) -> None:
        """Enqueue screening_id for background processing."""
        ...


@runtime_checkable
class IOcrService(Protocol):
    async def extract_text(self, document_bytes: bytes, document_type: str) -> Dict[str, Any]:
        """Extract text and MRZ data from document image."""
        ...


@runtime_checkable
class IDocumentValidator(Protocol):
    async def validate(self, extracted_fields: Dict[str, Any], document_type: str) -> List[Dict[str, Any]]:
        """Validate structure, checksums, validity dates, etc."""
        ...


@runtime_checkable
class ITamperDetector(Protocol):
    async def detect_tampering(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Run ELA and noise analysis for possible tampering."""
        ...


@runtime_checkable
class IFaceVerifier(Protocol):
    async def verify_face(self, document_image_bytes: bytes) -> List[Dict[str, Any]]:
        """Verify presence and quality of holder photo."""
        ...


@runtime_checkable
class IWatchlistService(Protocol):
    async def check_watchlist(self, extracted_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check extracted holder against watchlists."""
        ...

