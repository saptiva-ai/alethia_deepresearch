"""
Ports package for the Aletheia project.

This package contains all the port interfaces that define the contracts
for external adapters in the hexagonal architecture.
"""

from .browser_port import BrowserPort
from .doc_extract_port import DocExtractPort
from .guard_port import GuardAction, GuardPort, GuardResult
from .logging_port import LoggingPort, LogLevel
from .model_client_port import ModelClientPort
from .search_port import SearchPort
from .storage_port import StorageMetadata, StoragePort
from .vector_store_port import VectorStorePort

__all__ = [
    # Core ports
    "VectorStorePort",
    "ModelClientPort",
    "SearchPort",
    "BrowserPort",
    "DocExtractPort",
    "GuardPort",
    "LoggingPort",
    "StoragePort",
    # Supporting classes
    "GuardAction",
    "GuardResult",
    "LogLevel",
    "StorageMetadata",
]
