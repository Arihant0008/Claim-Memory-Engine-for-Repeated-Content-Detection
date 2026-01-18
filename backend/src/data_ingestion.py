"""
Data Ingestion Pipeline
Loads curated datasets into Qdrant for the claims memory.
"""

import random
from datetime import datetime, timedelta
from typing import Generator

from tqdm import tqdm

from .config import (
    FEVER_SAMPLE_SIZE, LIAR_SAMPLE_SIZE, SCIFACT_SAMPLE_SIZE,
    VERDICT_TRUE, VERDICT_FALSE, VERDICT_UNCERTAIN
)
from .agents.memory import MemoryUpdateAgent


# Mapping from dataset labels to our verdict format
FEVER_LABEL_MAP = {
    "SUPPORTS": VERDICT_TRUE,
    "REFUTES": VERDICT_FALSE,
    "NOT ENOUGH INFO": VERDICT_UNCERTAIN
}

LIAR_LABEL_MAP = {
    "true": VERDICT_TRUE,
    "mostly-true": VERDICT_TRUE,
    "half-true": VERDICT_UNCERTAIN,
    "barely-true": VERDICT_FALSE,
    "false": VERDICT_FALSE,
    "pants-fire": VERDICT_FALSE
}


def generate_random_timestamp(days_back: int = 7) -> str:
    """Generate a random timestamp within the last N days (default: 7 for fresh cache)."""
    random_days = random.randint(0, days_back)
    date = datetime.now() - timedelta(days=random_days)
    return date.isoformat()


def load_fever_dataset(sample_size: int = FEVER_SAMPLE_SIZE) -> Generator[dict, None, None]:
    """
    Load FEVER dataset from HuggingFace.
    
    FEVER (Fact Extraction and VERification) contains claims
    derived from Wikipedia with evidence.
    """
    try:
        from datasets import load_dataset
        
        print(f"Loading FEVER dataset (sampling {sample_size} claims)...")
        
        # Stream to avoid downloading full dataset
        dataset = load_dataset("fever", "v1.0", split="train", streaming=True)
        
        # Collect samples with balanced labels
        samples = {VERDICT_TRUE: [], VERDICT_FALSE: [], VERDICT_UNCERTAIN: []}
        target_per_label = sample_size // 3
        
        for item in dataset:
            label = FEVER_LABEL_MAP.get(item.get("label", ""), VERDICT_UNCERTAIN)
            
            if len(samples[label]) < target_per_label:
                samples[label].append(item)
            
            # Check if we have enough
            if all(len(s) >= target_per_label for s in samples.values()):
                break
        
        # Yield formatted claims
        for label, items in samples.items():
            for item in items:
                yield {
                    "claim_text": item.get("claim", ""),
                    "verdict": label,
                    "confidence": 0.85,
                    "source": "FEVER",
                    "source_reliability": 0.9,
                    "topic": "general",
                    "timestamp": generate_random_timestamp(365)
                }
                
    except Exception as e:
        print(f"Error loading FEVER: {e}")
        # Yield fallback sample data
        yield from get_fallback_claims()


def load_liar_dataset(sample_size: int = LIAR_SAMPLE_SIZE) -> Generator[dict, None, None]:
    """
    Load LIAR dataset for political fact-checking.
    """
    try:
        from datasets import load_dataset
        
        print(f"Loading LIAR dataset (sampling {sample_size} claims)...")
        
        dataset = load_dataset("liar", split="train", streaming=True)
        
        count = 0
        for item in dataset:
            if count >= sample_size:
                break
            
            label_raw = item.get("label", 2)  # LIAR uses numeric labels
            label_names = ["false", "half-true", "mostly-true", "true", "barely-true", "pants-fire"]
            
            if isinstance(label_raw, int) and label_raw < len(label_names):
                label_name = label_names[label_raw]
            else:
                label_name = "half-true"
            
            verdict = LIAR_LABEL_MAP.get(label_name, VERDICT_UNCERTAIN)
            
            yield {
                "claim_text": item.get("statement", ""),
                "verdict": verdict,
                "confidence": 0.80,
                "source": "LIAR-PolitiFact",
                "source_reliability": 0.85,
                "topic": "politics",
                "timestamp": generate_random_timestamp(730)  # 2 years back
            }
            
            count += 1
            
    except Exception as e:
        print(f"Error loading LIAR: {e}")


def get_fallback_claims() -> Generator[dict, None, None]:
    """
    Fallback claims when datasets cannot be loaded.
    Contains common misinformation claims for demonstration.
    """
    fallback_data = [
        # False claims - Health
        {"claim_text": "Vaccines cause autism in children", "verdict": VERDICT_FALSE, "topic": "health"},
        {"claim_text": "5G technology causes COVID-19", "verdict": VERDICT_FALSE, "topic": "health"},
        {"claim_text": "Drinking bleach cures COVID-19", "verdict": VERDICT_FALSE, "topic": "health"},
        {"claim_text": "Vaccines contain microchips for tracking", "verdict": VERDICT_FALSE, "topic": "health"},
        {"claim_text": "Face masks cause oxygen deficiency", "verdict": VERDICT_FALSE, "topic": "health"},
        {"claim_text": "Hydroxychloroquine cures COVID-19", "verdict": VERDICT_FALSE, "topic": "health"},
        {"claim_text": "COVID-19 vaccines alter human DNA", "verdict": VERDICT_FALSE, "topic": "health"},
        {"claim_text": "Vitamin C megadoses cure cancer", "verdict": VERDICT_FALSE, "topic": "health"},
        
        # False claims - Science
        {"claim_text": "The Earth is flat", "verdict": VERDICT_FALSE, "topic": "science"},
        {"claim_text": "Climate change is a hoax", "verdict": VERDICT_FALSE, "topic": "science"},
        {"claim_text": "Humans and dinosaurs coexisted", "verdict": VERDICT_FALSE, "topic": "science"},
        {"claim_text": "The moon landing was faked", "verdict": VERDICT_FALSE, "topic": "science"},
        {"claim_text": "Evolution is just a theory not supported by evidence", "verdict": VERDICT_FALSE, "topic": "science"},
        {"claim_text": "Wind turbines cause cancer", "verdict": VERDICT_FALSE, "topic": "science"},
        {"claim_text": "GMO foods cause cancer", "verdict": VERDICT_FALSE, "topic": "science"},
        
        # False claims - Politics
        {"claim_text": "Election voting machines are rigged", "verdict": VERDICT_FALSE, "topic": "politics"},
        {"claim_text": "Mail-in voting leads to massive fraud", "verdict": VERDICT_FALSE, "topic": "politics"},
        
        # True claims - Health
        {"claim_text": "Vaccines are safe and effective according to scientific consensus", "verdict": VERDICT_TRUE, "topic": "health"},
        {"claim_text": "Smoking causes lung cancer", "verdict": VERDICT_TRUE, "topic": "health"},
        {"claim_text": "Regular exercise improves cardiovascular health", "verdict": VERDICT_TRUE, "topic": "health"},
        {"claim_text": "The COVID-19 vaccines reduce severe illness and death", "verdict": VERDICT_TRUE, "topic": "health"},
        {"claim_text": "Antibiotics are ineffective against viral infections", "verdict": VERDICT_TRUE, "topic": "health"},
        {"claim_text": "Hand washing reduces the spread of infectious diseases", "verdict": VERDICT_TRUE, "topic": "health"},
        
        # True claims - Science
        {"claim_text": "Climate change is caused by human activity", "verdict": VERDICT_TRUE, "topic": "science"},
        {"claim_text": "The Earth is approximately 4.5 billion years old", "verdict": VERDICT_TRUE, "topic": "science"},
        {"claim_text": "Water is composed of hydrogen and oxygen", "verdict": VERDICT_TRUE, "topic": "science"},
        {"claim_text": "Humans evolved from earlier primate species", "verdict": VERDICT_TRUE, "topic": "science"},
        {"claim_text": "The speed of light is approximately 300,000 km per second", "verdict": VERDICT_TRUE, "topic": "science"},
        {"claim_text": "DNA carries genetic information in all living organisms", "verdict": VERDICT_TRUE, "topic": "science"},
        {"claim_text": "The universe began with the Big Bang approximately 13.8 billion years ago", "verdict": VERDICT_TRUE, "topic": "science"},
        
        # True claims - General
        {"claim_text": "The Great Wall of China is visible from low Earth orbit", "verdict": VERDICT_TRUE, "topic": "general"},
        {"claim_text": "Mount Everest is the highest mountain above sea level", "verdict": VERDICT_TRUE, "topic": "general"},
        
        # Uncertain claims
        {"claim_text": "Moderate coffee consumption may reduce risk of certain diseases", "verdict": VERDICT_UNCERTAIN, "topic": "health"},
        {"claim_text": "Artificial intelligence may surpass human intelligence in some domains", "verdict": VERDICT_UNCERTAIN, "topic": "science"},
        {"claim_text": "Social media use affects mental health in teenagers", "verdict": VERDICT_UNCERTAIN, "topic": "health"},
        {"claim_text": "Electric vehicles are better for the environment than gas cars", "verdict": VERDICT_UNCERTAIN, "topic": "science"},
    ]
    
    for claim in fallback_data:
        yield {
            "claim_text": claim["claim_text"],
            "verdict": claim["verdict"],
            "confidence": 0.90 if claim["verdict"] != VERDICT_UNCERTAIN else 0.60,
            "source": "Curated-Facts",
            "source_reliability": 0.95,
            "topic": claim["topic"],
            "timestamp": generate_random_timestamp(365)
        }


def ingest_all_datasets(use_real_datasets: bool = True) -> dict:
    """
    Ingest all datasets into Qdrant.
    
    Args:
        use_real_datasets: Whether to try loading real HuggingFace datasets
        
    Returns:
        Dictionary with ingestion statistics
    """
    memory_agent = MemoryUpdateAgent()
    
    # Ensure collection exists
    memory_agent.ensure_collection_exists()
    
    all_claims = []
    
    if use_real_datasets:
        try:
            # Try to load FEVER
            print("\n📊 Loading FEVER dataset...")
            fever_claims = list(load_fever_dataset(FEVER_SAMPLE_SIZE))
            all_claims.extend(fever_claims)
            print(f"   Loaded {len(fever_claims)} claims from FEVER")
        except Exception as e:
            print(f"   ⚠️ Could not load FEVER: {e}")
        
        try:
            # Try to load LIAR
            print("\n📊 Loading LIAR dataset...")
            liar_claims = list(load_liar_dataset(LIAR_SAMPLE_SIZE))
            all_claims.extend(liar_claims)
            print(f"   Loaded {len(liar_claims)} claims from LIAR")
        except Exception as e:
            print(f"   ⚠️ Could not load LIAR: {e}")
    
    # Always add fallback claims
    print("\n📊 Loading curated claims...")
    fallback = list(get_fallback_claims())
    all_claims.extend(fallback)
    print(f"   Loaded {len(fallback)} curated claims")
    
    # Remove duplicates by claim text
    seen = set()
    unique_claims = []
    for claim in all_claims:
        text = claim["claim_text"].lower().strip()
        if text not in seen and text:
            seen.add(text)
            unique_claims.append(claim)
    
    print(f"\n📝 Total unique claims: {len(unique_claims)}")
    
    # Batch upsert
    print("\n🚀 Ingesting into Qdrant...")
    result = memory_agent.batch_upsert(unique_claims, show_progress=True)
    
    print(f"\n✅ Ingestion complete!")
    print(f"   Success: {result['success_count']}")
    print(f"   Errors: {result['error_count']}")
    
    # Get final stats
    stats = memory_agent.retriever.get_collection_stats()
    print(f"\n📈 Collection stats: {stats}")
    
    return {
        "total_processed": len(unique_claims),
        "success_count": result["success_count"],
        "error_count": result["error_count"],
        "collection_stats": stats
    }


if __name__ == "__main__":
    print("=" * 60)
    print("PCM Data Ingestion Pipeline")
    print("=" * 60)
    
    result = ingest_all_datasets(use_real_datasets=True)
    
    print("\n" + "=" * 60)
    print("Final Summary:")
    print(f"  Total claims processed: {result['total_processed']}")
    print(f"  Successfully ingested: {result['success_count']}")
    print(f"  Collection size: {result['collection_stats'].get('total_claims', 0)}")
    print("=" * 60)
