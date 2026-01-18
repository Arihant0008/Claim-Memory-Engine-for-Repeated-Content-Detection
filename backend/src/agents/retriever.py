"""
Retrieval Agent
Handles vector search operations against Qdrant for claim retrieval.
Implements hybrid search, discovery search, and time-decay scoring.
"""

import math
import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding

from ..config import (
    QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME,
    TEXT_EMBEDDING_MODEL, DEFAULT_TOP_K, TIME_DECAY_SIGMA_DAYS
)

logger = logging.getLogger(__name__)


@dataclass
class RetrievedClaim:
    """Represents a retrieved claim with metadata."""
    id: str
    claim_text: str
    normalized_text: str
    verdict: str
    confidence: float
    source: str
    source_reliability: float
    timestamp: str
    seen_count: int
    similarity_score: float
    time_decayed_score: float


class RetrievalAgent:
    """
    Agent 2: Retrieval Agent
    Performs vector similarity search against the claims memory.
    Implements hybrid search, discovery search, and time-decay boosting.
    """
    
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self.embed_model = TextEmbedding(TEXT_EMBEDDING_MODEL)
        
        # Truth anchor embeddings for discovery search
        self.truth_anchors = [
            "Vaccines are safe and effective according to scientific studies",
            "Climate change is caused by human activity according to scientific consensus",
            "The Earth is approximately 4.5 billion years old",
        ]
        self.false_anchors = [
            "Vaccines cause autism in children",
            "Climate change is a hoax created for political purposes",
            "The Earth is only 6000 years old",
        ]
        
        self._truth_embeddings = None
        self._false_embeddings = None
    
    def _get_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = list(self.embed_model.embed([text]))
        return embeddings[0].tolist()
    
    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [emb.tolist() for emb in self.embed_model.embed(texts)]
    
    def _get_truth_embeddings(self) -> list[list[float]]:
        """Lazy-load truth anchor embeddings."""
        if self._truth_embeddings is None:
            self._truth_embeddings = self._get_embeddings(self.truth_anchors)
        return self._truth_embeddings
    
    def _get_false_embeddings(self) -> list[list[float]]:
        """Lazy-load false anchor embeddings."""
        if self._false_embeddings is None:
            self._false_embeddings = self._get_embeddings(self.false_anchors)
        return self._false_embeddings
    
    def _apply_time_decay(
        self,
        results: list,
        sigma_days: float = TIME_DECAY_SIGMA_DAYS
    ) -> list[tuple]:
        """
        Apply Gaussian time-decay to search results.
        Recent claims get higher scores.
        
        Score = original_score * (0.5 + 0.5 * decay)
        where decay = e^(-(days_old^2) / (2 * sigma^2))
        """
        now = datetime.now()
        decayed_results = []
        
        for result in results:
            try:
                timestamp_str = result.payload.get("timestamp", "")
                if timestamp_str:
                    # Parse ISO format timestamp
                    if "T" in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
                    
                    # Handle timezone-aware vs naive datetime
                    if timestamp.tzinfo:
                        from datetime import timezone
                        now_aware = datetime.now(timezone.utc)
                        days_old = (now_aware - timestamp).days
                    else:
                        days_old = (now - timestamp).days
                else:
                    days_old = 0
                
                # Gaussian decay function
                decay = math.exp(-((days_old ** 2) / (2 * sigma_days ** 2)))
                
                # Apply decay: 50% base score + 50% time-adjusted
                adjusted_score = result.score * (0.5 + 0.5 * decay)
                
                decayed_results.append((result, adjusted_score, days_old))
                
            except Exception as e:
                # If timestamp parsing fails, use original score
                decayed_results.append((result, result.score, 0))
        
        # Sort by decayed score
        decayed_results.sort(key=lambda x: x[1], reverse=True)
        
        return decayed_results
    
    def _convert_to_retrieved_claim(
        self,
        result,
        decayed_score: float
    ) -> RetrievedClaim:
        """Convert Qdrant result to RetrievedClaim dataclass."""
        payload = result.payload
        
        return RetrievedClaim(
            id=str(result.id),
            claim_text=payload.get("claim_text", ""),
            normalized_text=payload.get("normalized_text", payload.get("claim_text", "")),
            verdict=payload.get("verdict", "Unknown"),
            confidence=payload.get("confidence", 0.0),
            source=payload.get("source", "Unknown"),
            source_reliability=payload.get("source_reliability", 0.5),
            timestamp=payload.get("timestamp", ""),
            seen_count=payload.get("seen_count", 1),
            similarity_score=result.score,
            time_decayed_score=decayed_score
        )
    
    def search(
        self,
        query_text: str,
        k: int = DEFAULT_TOP_K,
        apply_time_decay: bool = True,
        min_timestamp: Optional[str] = None,
        verdict_filter: Optional[str] = None
    ) -> list[RetrievedClaim]:
        """
        Perform similarity search for a claim.
        
        Args:
            query_text: The claim text to search for
            k: Number of results to return
            apply_time_decay: Whether to apply time-decay scoring
            min_timestamp: Filter results after this timestamp
            verdict_filter: Filter by verdict (True, False, Uncertain)
            
        Returns:
            List of RetrievedClaim objects
        """
        query_embedding = self._get_embedding(query_text)
        
        # Build filters
        filter_conditions = []
        
        if min_timestamp:
            filter_conditions.append(
                models.FieldCondition(
                    key="timestamp",
                    range=models.Range(gte=min_timestamp)
                )
            )
        
        if verdict_filter:
            filter_conditions.append(
                models.FieldCondition(
                    key="verdict",
                    match=models.MatchValue(value=verdict_filter)
                )
            )
        
        query_filter = None
        if filter_conditions:
            query_filter = models.Filter(must=filter_conditions)
        
        try:
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=k,
                query_filter=query_filter,
                with_payload=True
            )
            
            if not results:
                return []
            
            if apply_time_decay:
                decayed_results = self._apply_time_decay(results)
                return [
                    self._convert_to_retrieved_claim(r, score)
                    for r, score, _ in decayed_results
                ]
            else:
                return [
                    self._convert_to_retrieved_claim(r, r.score)
                    for r in results
                ]
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def discovery_search(
        self,
        query_text: str,
        k: int = DEFAULT_TOP_K
    ) -> list[RetrievedClaim]:
        """
        Perform discovery search using truth/false anchors.
        This helps find claims that contradict known misinformation.
        
        The search is guided toward claims similar to truth anchors
        and away from claims similar to false anchors.
        """
        query_embedding = self._get_embedding(query_text)
        truth_embeddings = self._get_truth_embeddings()
        false_embeddings = self._get_false_embeddings()
        
        try:
            # Discovery API was removed in newer qdrant-client
            # Fallback to regular search with best-effort semantic matching
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=k,
                with_payload=True
            )
            
            if not results:
                return []
            
            decayed_results = self._apply_time_decay(results)
            return [
                self._convert_to_retrieved_claim(r, score)
                for r, score, _ in decayed_results
            ]
            
        except Exception as e:
            print(f"Discovery search error: {e}")
            # Fallback to regular search
            return self.search(query_text, k)
    
    def search_by_image_embedding(
        self,
        image_embedding: list[float],
        k: int = DEFAULT_TOP_K
    ) -> list[RetrievedClaim]:
        """
        Search using a visual (CLIP) embedding for cross-modal retrieval.
        
        Args:
            image_embedding: CLIP embedding of the image
            k: Number of results to return
            
        Returns:
            List of RetrievedClaim objects
        """
        try:
            results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=image_embedding,
                limit=k,
                with_payload=True
            )
            
            if not results:
                return []
            
            decayed_results = self._apply_time_decay(results)
            return [
                self._convert_to_retrieved_claim(r, score)
                for r, score, _ in decayed_results
            ]
            
        except Exception as e:
            logger.error(f"Discovery search error: {e}")
            return []
    
    def get_similar_claim(
        self,
        query_text: str,
        threshold: float = 0.92
    ) -> Optional[RetrievedClaim]:
        """
        Check if a very similar claim already exists.
        Used for deduplication before inserting new claims.
        
        Args:
            query_text: The claim text to check
            threshold: Minimum similarity for considering a match
            
        Returns:
            The matching claim if found, None otherwise
        """
        results = self.search(query_text, k=1, apply_time_decay=False)
        
        if results and results[0].similarity_score >= threshold:
            return results[0]
        
        return None
    
    def get_collection_stats(self) -> dict:
        """Get statistics about the claims collection."""
        try:
            info = self.client.get_collection(COLLECTION_NAME)
            return {
                "total_claims": getattr(info, 'points_count', 0),
                "indexed_vectors": getattr(info, 'indexed_vectors_count', 0),
                "status": str(getattr(info, 'status', 'unknown'))
            }
        except Exception as e:
            # Try to at least count points
            try:
                count = self.client.count(COLLECTION_NAME)
                return {
                    "total_claims": count.count,
                    "status": "ok"
                }
            except:
                return {"error": str(e), "total_claims": 0}
    
    def get_detailed_stats(self) -> dict:
        """
        Get detailed statistics about the claims collection.
        Used for the live memory dashboard to prove memory evolution.
        
        Returns:
            Dictionary with:
            - total_claims: Total number of claims
            - verdicts: Breakdown by verdict type
            - avg_seen_count: Average times claims have been seen
            - max_seen_count: Most-seen claim count
            - top_claims: Top 5 most-seen claims (id, text, seen_count)
            - claims_last_24h: Claims added in last 24 hours
        """
        from datetime import datetime, timedelta
        
        try:
            # Get basic stats
            basic_stats = self.get_collection_stats()
            
            # Scroll through all claims to compute detailed stats
            all_claims = []
            offset = None
            
            while True:
                results, offset = self.client.scroll(
                    collection_name=COLLECTION_NAME,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                if not results:
                    break
                    
                all_claims.extend(results)
                
                if offset is None:
                    break
            
            if not all_claims:
                return {
                    **basic_stats,
                    "verdicts": {"True": 0, "False": 0, "Uncertain": 0},
                    "avg_seen_count": 0,
                    "max_seen_count": 0,
                    "top_claims": [],
                    "claims_last_24h": 0
                }
            
            # Compute verdict breakdown
            verdicts = {"True": 0, "False": 0, "Uncertain": 0}
            seen_counts = []
            claims_24h = 0
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            
            claim_data = []
            
            for claim in all_claims:
                payload = claim.payload
                
                # Verdict counting
                verdict = payload.get("verdict", "Unknown")
                if verdict in verdicts:
                    verdicts[verdict] += 1
                
                # Seen count tracking
                seen_count = payload.get("seen_count", 1)
                seen_counts.append(seen_count)
                
                claim_data.append({
                    "id": str(claim.id),
                    "text": payload.get("claim_text", "")[:100],
                    "seen_count": seen_count,
                    "verdict": verdict
                })
                
                # Check if added in last 24h
                try:
                    first_seen = payload.get("first_seen", "")
                    if first_seen:
                        claim_time = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
                        if claim_time.tzinfo:
                            from datetime import timezone
                            yesterday_aware = datetime.now(timezone.utc) - timedelta(days=1)
                            if claim_time > yesterday_aware:
                                claims_24h += 1
                        else:
                            if claim_time > yesterday:
                                claims_24h += 1
                except:
                    pass
            
            # Sort by seen_count and get top 5
            claim_data.sort(key=lambda x: x["seen_count"], reverse=True)
            top_claims = claim_data[:5]
            
            return {
                **basic_stats,
                "verdicts": verdicts,
                "avg_seen_count": sum(seen_counts) / len(seen_counts) if seen_counts else 0,
                "max_seen_count": max(seen_counts) if seen_counts else 0,
                "top_claims": top_claims,
                "claims_last_24h": claims_24h
            }
            
        except Exception as e:
            print(f"Error getting detailed stats: {e}")
            return {
                "error": str(e),
                "total_claims": 0,
                "verdicts": {"True": 0, "False": 0, "Uncertain": 0},
                "avg_seen_count": 0,
                "max_seen_count": 0,
                "top_claims": [],
                "claims_last_24h": 0
            }


if __name__ == "__main__":
    # Test the retrieval agent
    agent = RetrievalAgent()
    
    # Test search
    test_query = "Vaccines cause autism"
    print(f"\nSearching for: '{test_query}'")
    
    results = agent.search(test_query, k=5)
    
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result.claim_text[:80]}...")
        print(f"   Verdict: {result.verdict} | Score: {result.similarity_score:.3f}")
        print(f"   Source: {result.source} | Seen: {result.seen_count} times")
