"""
Memory Update Agent
Handles persistent storage and updates to the claims memory in Qdrant.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding

from ..config import (
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    TEXT_EMBEDDING_MODEL, TEXT_EMBEDDING_DIM, VISUAL_EMBEDDING_DIM,
    SIMILARITY_THRESHOLD
)
from .retriever import RetrievalAgent
from .reasoner import VerificationResult

logger = logging.getLogger(__name__)


@dataclass
class MemoryUpdateResult:
    """Result of a memory update operation."""
    action: str  # "created", "updated", "skipped"
    claim_id: str
    seen_count: int
    message: str


class MemoryUpdateAgent:
    """
    Agent 4: Memory Update Agent
    Manages the persistent memory of verified claims.
    Handles deduplication, updates, and insertions.
    """
    
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.embed_model = TextEmbedding(TEXT_EMBEDDING_MODEL)
        self.retriever = RetrievalAgent()
    
    def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = list(self.embed_model.embed([text]))
        return embeddings[0].tolist()
    
    def _generate_id(self) -> str:
        """Generate a unique ID for a new claim."""
        return uuid.uuid4().hex
    
    def ensure_collection_exists(self) -> bool:
        """
        Ensure the claims collection exists with proper schema.
        Creates it if it doesn't exist.
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if COLLECTION_NAME in collection_names:
                return True
            
            # Create collection with named vectors (simplified for cloud tier)
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config={
                    "dense_text": models.VectorParams(
                        size=TEXT_EMBEDDING_DIM,
                        distance=models.Distance.COSINE
                    ),
                    "visual": models.VectorParams(
                        size=VISUAL_EMBEDDING_DIM,
                        distance=models.Distance.COSINE
                    )
                }
            )
            
            # Create payload indexes for efficient filtering
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="verdict",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="topic",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            self.client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="source",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            print(f"Created collection '{COLLECTION_NAME}' with indexes")
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            return False
    
    def update_or_create(
        self,
        verification_result: VerificationResult,
        topic: Optional[str] = None,
        visual_embedding: Optional[list[float]] = None
    ) -> MemoryUpdateResult:
        """
        Update existing claim or create new one based on similarity.
        
        If a very similar claim exists (>0.92 similarity):
            - Update seen_count and last_seen
        Otherwise:
            - Create new claim entry
            
        Args:
            verification_result: The verification result to store
            topic: Optional topic category
            visual_embedding: Optional CLIP embedding for images
            
        Returns:
            MemoryUpdateResult with action taken
        """
        claim_embedding = self._get_embedding(verification_result.normalized_claim)
        
        # Check for existing similar claim
        existing = self.retriever.get_similar_claim(
            verification_result.normalized_claim,
            threshold=SIMILARITY_THRESHOLD
        )
        
        now = datetime.now().isoformat()
        
        if existing:
            # Update existing claim
            new_seen_count = existing.seen_count + 1
            
            try:
                self.client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload={
                        "seen_count": new_seen_count,
                        "last_seen": now,
                        # Optionally update confidence based on repeated verification
                        "confidence": max(existing.confidence, verification_result.confidence)
                    },
                    points=[existing.id]
                )
                
                return MemoryUpdateResult(
                    action="updated",
                    claim_id=existing.id,
                    seen_count=new_seen_count,
                    message=f"Updated existing claim. Seen {new_seen_count} times."
                )
                
            except Exception as e:
                logger.error(f"Error updating claim: {e}")
                return MemoryUpdateResult(
                    action="skipped",
                    claim_id=existing.id,
                    seen_count=existing.seen_count,
                    message=f"Failed to update: {str(e)}"
                )
        else:
            # Create new claim
            claim_id = self._generate_id()
            
            # Prepare vectors
            vectors = {"dense_text": claim_embedding}
            if visual_embedding:
                vectors["visual"] = visual_embedding
            
            # Prepare payload
            payload = {
                "claim_text": verification_result.claim_text,
                "normalized_text": verification_result.normalized_claim,
                "verdict": verification_result.verdict,
                "confidence": verification_result.confidence,
                "explanation": verification_result.explanation,
                "evidence_ids": verification_result.evidence_ids,
                "source": "user_verification",
                "source_reliability": 0.7,  # Default for user submissions
                "timestamp": now,
                "first_seen": now,
                "last_seen": now,
                "seen_count": 1
            }
            
            if topic:
                payload["topic"] = topic
            
            try:
                self.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[
                        models.PointStruct(
                            id=claim_id,
                            vector=vectors,
                            payload=payload
                        )
                    ]
                )
                
                return MemoryUpdateResult(
                    action="created",
                    claim_id=claim_id,
                    seen_count=1,
                    message="New claim added to memory."
                )
                
            except Exception as e:
                logger.error(f"Error creating claim: {e}")
                return MemoryUpdateResult(
                    action="skipped",
                    claim_id="",
                    seen_count=0,
                    message=f"Failed to create: {str(e)}"
                )
    
    def batch_upsert(
        self,
        claims_data: list[dict],
        show_progress: bool = True
    ) -> dict:
        """
        Batch upsert multiple claims for initial data ingestion.
        
        Args:
            claims_data: List of claim dictionaries with keys:
                - claim_text: The claim text
                - verdict: True/False/Uncertain
                - source: Source name
                - source_reliability: 0.0-1.0
                - topic: Optional topic category
                - timestamp: Optional ISO timestamp
            show_progress: Whether to show progress bar
            
        Returns:
            Dictionary with success count and errors
        """
        from tqdm import tqdm
        
        self.ensure_collection_exists()
        
        points = []
        errors = []
        
        iterator = tqdm(claims_data, desc="Embedding claims") if show_progress else claims_data
        
        for i, claim in enumerate(iterator):
            try:
                claim_text = claim.get("claim_text", "")
                if not claim_text:
                    errors.append({"index": i, "error": "Empty claim text"})
                    continue
                
                embedding = self._get_embedding(claim_text)
                now = datetime.now().isoformat()
                
                points.append(
                    models.PointStruct(
                        id=self._generate_id(),
                        vector={"dense_text": embedding},
                        payload={
                            "claim_text": claim_text,
                            "normalized_text": claim_text,  # Pre-normalized in dataset
                            "verdict": claim.get("verdict", "Unknown"),
                            "confidence": claim.get("confidence", 0.8),
                            "source": claim.get("source", "Unknown"),
                            "source_reliability": claim.get("source_reliability", 0.7),
                            "topic": claim.get("topic", "general"),
                            "timestamp": claim.get("timestamp", now),
                            "first_seen": now,
                            "last_seen": now,
                            "seen_count": 1
                        }
                    )
                )
                
            except Exception as e:
                errors.append({"index": i, "error": str(e)})
        
        # Batch upsert in chunks
        batch_size = 100
        success_count = 0
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            try:
                self.client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch
                )
                success_count += len(batch)
            except Exception as e:
                errors.append({"batch": i // batch_size, "error": str(e)})
        
        return {
            "success_count": success_count,
            "error_count": len(errors),
            "errors": errors
        }
    
    def get_top_claims(self, limit: int = 10, order_by: str = "seen_count") -> list[dict]:
        """
        Get top claims by specified ordering.
        
        Args:
            limit: Number of claims to return
            order_by: Field to order by (seen_count, timestamp)
            
        Returns:
            List of claim dictionaries
        """
        try:
            # Scroll through claims (fetch more than needed, then sort)
            results, _ = self.client.scroll(
                collection_name=COLLECTION_NAME,
                limit=limit * 3,  # Fetch extra for sorting
                with_payload=True,
                with_vectors=False
            )
            
            # Convert to list and sort by order_by field
            claims = [
                {
                    "id": str(r.id),
                    **r.payload
                }
                for r in results
            ]
            
            # Sort by specified field
            claims.sort(key=lambda x: x.get(order_by, 0), reverse=True)
            
            return claims[:limit]
            
        except Exception as e:
            logger.error(f"Error getting top claims: {e}")
            return []
    
    def delete_claim(self, claim_id: str) -> bool:
        """Delete a claim by ID."""
        try:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.PointIdsList(points=[claim_id])
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting claim: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """Delete and recreate the collection. Use with caution!"""
        try:
            self.client.delete_collection(COLLECTION_NAME)
            return self.ensure_collection_exists()
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False


if __name__ == "__main__":
    # Test the memory agent
    agent = MemoryUpdateAgent()
    
    # Ensure collection exists
    agent.ensure_collection_exists()
    
    # Get stats
    stats = agent.retriever.get_collection_stats()
    print(f"Collection stats: {stats}")
    
    # Get top claims
    top = agent.get_top_claims(limit=5)
    print(f"\nTop claims: {len(top)}")
    for claim in top:
        print(f"  - {claim.get('claim_text', '')[:50]}...")
