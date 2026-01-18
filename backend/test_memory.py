"""
Test memory functionality
"""
import sys
from src.agents.memory import MemoryUpdateAgent
from src.agents.retriever import RetrievalAgent
from src.agents.reasoner import VerificationResult

print("Testing memory functionality...\n")

# Check collection stats
retriever = RetrievalAgent()
stats = retriever.get_collection_stats()
print(f"Collection stats: {stats}\n")

# Search for Harris claims
print("Searching for 'Kamala Harris' claims...")
results = retriever.search("Kamala Harris is president", k=5)
print(f"Found {len(results)} similar claims\n")

for i, r in enumerate(results, 1):
    print(f"{i}. {r.claim_text}")
    print(f"   Similarity: {r.similarity_score:.3f}")
    print(f"   Verdict: {r.verdict}")
    print(f"   Source: {r.source}")
    print(f"   Seen: {r.seen_count} times\n")

# Test if memory updates are working
print("\n" + "="*60)
print("Testing memory update...")
print("="*60)

memory_agent = MemoryUpdateAgent()
test_result = VerificationResult(
    claim_text="Test claim for memory",
    normalized_claim="test claim for memory",
    verdict="False",
    confidence=0.95,
    explanation="This is a test",
    evidence_ids=[],
    evidence_summary="Test",
    reasoning_trace="Test reasoning"
)

update_result = memory_agent.update_or_create(test_result)
print(f"\nMemory update result:")
print(f"  Action: {update_result.action}")
print(f"  Claim ID: {update_result.claim_id}")
print(f"  Seen count: {update_result.seen_count}")
print(f"  Message: {update_result.message}")

# Check updated stats
new_stats = retriever.get_collection_stats()
print(f"\nUpdated collection stats: {new_stats}")
