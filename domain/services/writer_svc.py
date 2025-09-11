import os
import hashlib
from typing import List
from domain.models.evidence import Evidence
from adapters.saptiva_model.saptiva_client import SaptivaModelAdapter
from adapters.weaviate_vector.weaviate_adapter import WeaviateVectorAdapter
from ports.vector_store_port import VectorStorePort

class WriterService:
    def __init__(self):
        self.model_adapter = SaptivaModelAdapter()
        # As per README, Writer uses 'Saptiva Cortex'
        self.writer_model = os.getenv("SAPTIVA_MODEL_WRITER", "Saptiva Cortex")
        
        # Initialize vector store for RAG
        self.vector_store: VectorStorePort = WeaviateVectorAdapter()

    def write_report(self, query: str, evidence_list: List[Evidence]) -> str:
        """
        Generates a markdown report based on the collected evidence.
        Now enhanced with RAG retrieval for additional context.
        """
        # Get collection name based on query
        collection_name = f"research_{self._generate_collection_id(query)}"
        
        # Enhance evidence with RAG retrieval
        enhanced_evidence = self._enhance_with_rag(query, evidence_list, collection_name)
        
        prompt = self._build_prompt(query, enhanced_evidence)
        
        response = self.model_adapter.generate(
            model=self.writer_model,
            prompt=prompt,
            max_tokens=3000,
            temperature=0.7
        )
        
        return response.get("content", "# Empty Report")

    def _enhance_with_rag(self, query: str, evidence_list: List[Evidence], collection_name: str) -> List[Evidence]:
        """
        Enhance the evidence list with additional context from vector store.
        """
        # Search for additional relevant evidence
        additional_evidence = self.vector_store.search_similar(query, collection_name, limit=10)
        
        # Deduplicate by hash or ID
        seen_hashes = set()
        seen_ids = set()
        
        # Add original evidence first
        for ev in evidence_list:
            seen_ids.add(ev.id)
            if ev.hash:
                seen_hashes.add(ev.hash)
        
        # Add non-duplicate additional evidence
        enhanced_list = evidence_list.copy()
        for ev in additional_evidence:
            if ev.id not in seen_ids and (not ev.hash or ev.hash not in seen_hashes):
                enhanced_list.append(ev)
                seen_ids.add(ev.id)
                if ev.hash:
                    seen_hashes.add(ev.hash)
        
        print(f"Enhanced evidence: {len(evidence_list)} original + {len(enhanced_list) - len(evidence_list)} from RAG = {len(enhanced_list)} total")
        return enhanced_list

    def _build_prompt(self, query: str, evidence_list: List[Evidence]) -> str:
        evidence_str = "\n\n".join(
            [f"Source: {ev.source.url}\nTitle: {ev.source.title}\nExcerpt: {ev.excerpt}" for ev in evidence_list]
        )

        return f"""
Based on the following user query and the collected evidence, please write a comprehensive markdown report.
Cite the evidence by referencing the source URL in the format [Source](URL).

Use the following structure:
# {query}

## Executive Summary
[Brief summary of key findings]

## Key Findings
[Main insights from the research]

## Detailed Analysis
[In-depth analysis with citations]

## Conclusions
[Summary of conclusions and implications]

## Sources
[Bibliography of all sources used]

User Query: "{query}"

Evidence:
---
{evidence_str}
---

Markdown Report:
"""

    def _generate_collection_id(self, main_query: str) -> str:
        """Generate a unique collection ID based on the main query."""
        hash_obj = hashlib.md5(main_query.encode())
        return hash_obj.hexdigest()[:8]
