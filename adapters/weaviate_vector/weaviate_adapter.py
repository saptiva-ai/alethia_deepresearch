import os
import weaviate
from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime

from ports.vector_store_port import VectorStorePort
from domain.models.evidence import Evidence, EvidenceSource


class WeaviateVectorAdapter(VectorStorePort):
    """Weaviate implementation of VectorStorePort using v3 API."""
    
    def __init__(self):
        self.host = os.getenv("WEAVIATE_HOST", "http://localhost:8080")
        self.mock_mode = False
        
        try:
            # Try to connect to Weaviate using v3 API
            self.client = weaviate.Client(url=self.host)
            # Test connection
            if not self.health_check():
                print(f"Warning: Could not connect to Weaviate at {self.host}. Using mock mode.")
                self.mock_mode = True
                self.client = None
        except Exception as e:
            print(f"Warning: Weaviate connection failed: {e}. Using mock mode.")
            self.mock_mode = True
            self.client = None
            
        # Mock storage for when Weaviate is not available
        self.mock_store: Dict[str, List[Dict]] = {}
    
    def store_evidence(self, evidence: Evidence, collection_name: str = "default") -> bool:
        """Store evidence in Weaviate or mock storage."""
        if self.mock_mode:
            return self._mock_store_evidence(evidence, collection_name)
        
        try:
            # Create collection if it doesn't exist
            self.create_collection(collection_name)
            
            # Prepare data object (using evidence_id instead of id - reserved in Weaviate)
            data_object = {
                "evidence_id": evidence.id,
                "excerpt": evidence.excerpt,
                "source_url": evidence.source.url,
                "source_title": evidence.source.title,
                "fetched_at": evidence.source.fetched_at.isoformat(),
                "hash": evidence.hash or "",
                "tool_call_id": evidence.tool_call_id or "",
                "score": evidence.score or 0.0,
                "tags": evidence.tags or [],
                "cit_key": evidence.cit_key or ""
            }
            
            # Insert object with vector (Weaviate will auto-vectorize based on excerpt)
            self.client.data_object.create(
                data_object=data_object,
                class_name=collection_name,
                uuid=evidence.id
            )
            
            print(f"Stored evidence {evidence.id} in Weaviate collection {collection_name}")
            return True
            
        except Exception as e:
            print(f"Error storing evidence in Weaviate: {e}")
            return False
    
    def search_similar(self, query: str, collection_name: str = "default", limit: int = 5) -> List[Evidence]:
        """Search for similar evidence using semantic search."""
        if self.mock_mode:
            return self._mock_search_similar(query, collection_name, limit)
        
        try:
            # Perform semantic search using nearText
            response = (
                self.client.query
                .get(collection_name, [
                    "evidence_id", "excerpt", "source_url", "source_title", 
                    "fetched_at", "hash", "tool_call_id", "score", "tags", "cit_key"
                ])
                .with_near_text({
                    "concepts": [query]
                })
                .with_additional(["score"])
                .with_limit(limit)
                .do()
            )
            
            # Convert results to Evidence objects
            results = []
            if "data" in response and "Get" in response["data"] and collection_name in response["data"]["Get"]:
                for obj in response["data"]["Get"][collection_name]:
                    evidence = Evidence(
                        id=obj["evidence_id"],
                        source=EvidenceSource(
                            url=obj["source_url"],
                            title=obj["source_title"],
                            fetched_at=datetime.fromisoformat(obj["fetched_at"])
                        ),
                        excerpt=obj["excerpt"],
                        hash=obj.get("hash") or None,
                        tool_call_id=obj.get("tool_call_id") or None,
                        score=obj.get("_additional", {}).get("score", obj.get("score", 0.0)),
                        tags=obj.get("tags", []),
                        cit_key=obj.get("cit_key") or None
                    )
                    results.append(evidence)
            
            print(f"Found {len(results)} similar evidence items for query: {query}")
            return results
            
        except Exception as e:
            print(f"Error searching in Weaviate: {e}")
            return []
    
    def create_collection(self, collection_name: str) -> bool:
        """Create a Weaviate collection/class."""
        if self.mock_mode:
            self.mock_store[collection_name] = []
            return True
        
        try:
            # Check if collection already exists
            schema = self.client.schema.get()
            for class_obj in schema.get("classes", []):
                if class_obj["class"] == collection_name:
                    return True
            
            # Create collection with schema
            class_definition = {
                "class": collection_name,
                "description": f"Evidence collection for research task: {collection_name}",
                "properties": [
                    {"name": "evidence_id", "dataType": ["text"]},
                    {"name": "excerpt", "dataType": ["text"]},
                    {"name": "source_url", "dataType": ["text"]},
                    {"name": "source_title", "dataType": ["text"]},
                    {"name": "fetched_at", "dataType": ["text"]},
                    {"name": "hash", "dataType": ["text"]},
                    {"name": "tool_call_id", "dataType": ["text"]},
                    {"name": "score", "dataType": ["number"]},
                    {"name": "tags", "dataType": ["text[]"]},
                    {"name": "cit_key", "dataType": ["text"]},
                ]
            }
            
            self.client.schema.create_class(class_definition)
            print(f"Created Weaviate collection: {collection_name}")
            return True
            
        except Exception as e:
            print(f"Error creating Weaviate collection: {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a Weaviate collection."""
        if self.mock_mode:
            if collection_name in self.mock_store:
                del self.mock_store[collection_name]
            return True
        
        try:
            self.client.schema.delete_class(collection_name)
            print(f"Deleted Weaviate collection: {collection_name}")
            return True
            
        except Exception as e:
            print(f"Error deleting Weaviate collection: {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if Weaviate is available."""
        if self.mock_mode:
            return False
        
        try:
            if self.client is None:
                return False
            return self.client.is_ready()
        except Exception:
            return False
    
    # Mock methods for when Weaviate is not available
    def _mock_store_evidence(self, evidence: Evidence, collection_name: str) -> bool:
        """Mock storage for testing without Weaviate."""
        if collection_name not in self.mock_store:
            self.mock_store[collection_name] = []
        
        # Convert evidence to dict for storage
        evidence_dict = {
            "evidence_id": evidence.id,
            "excerpt": evidence.excerpt,
            "source_url": evidence.source.url,
            "source_title": evidence.source.title,
            "fetched_at": evidence.source.fetched_at.isoformat(),
            "hash": evidence.hash,
            "tool_call_id": evidence.tool_call_id,
            "score": evidence.score,
            "tags": evidence.tags,
            "cit_key": evidence.cit_key
        }
        
        self.mock_store[collection_name].append(evidence_dict)
        print(f"[MOCK] Stored evidence {evidence.id} in collection {collection_name}")
        return True
    
    def _mock_search_similar(self, query: str, collection_name: str, limit: int) -> List[Evidence]:
        """Mock search for testing without Weaviate."""
        if collection_name not in self.mock_store:
            return []
        
        # Simple keyword matching for mock
        results = []
        query_lower = query.lower()
        
        for evidence_dict in self.mock_store[collection_name]:
            if query_lower in evidence_dict["excerpt"].lower():
                evidence = Evidence(
                    id=evidence_dict["evidence_id"],
                    source=EvidenceSource(
                        url=evidence_dict["source_url"],
                        title=evidence_dict["source_title"],
                        fetched_at=datetime.fromisoformat(evidence_dict["fetched_at"])
                    ),
                    excerpt=evidence_dict["excerpt"],
                    hash=evidence_dict["hash"],
                    tool_call_id=evidence_dict["tool_call_id"],
                    score=evidence_dict["score"],
                    tags=evidence_dict["tags"],
                    cit_key=evidence_dict["cit_key"]
                )
                results.append(evidence)
                
                if len(results) >= limit:
                    break
        
        print(f"[MOCK] Found {len(results)} similar evidence items for query: {query}")
        return results