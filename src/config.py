"""
Configuration module for the PCM system.
Loads environment variables and provides centralized config.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "claims_memory"

# Groq Configuration (for Llama)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"

# Gemini removed - image processing disabled

# Tavily Configuration (for web search)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Embedding Configuration
TEXT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TEXT_EMBEDDING_DIM = 384
VISUAL_EMBEDDING_DIM = 512

# ==== Search Configuration ====
# These thresholds were empirically tested. See docs/THRESHOLDS.md for full justification.

# Deduplication threshold: When storing a new claim, we check if a near-identical
# claim exists. If similarity >= 0.92, we UPDATE the existing record instead of
# creating a duplicate. Very strict to avoid merging different claims.
# Example: "vaccines autism" vs "vaccines cancer" = 0.87 (should NOT merge)
SIMILARITY_THRESHOLD = 0.92

# Cache hit threshold: When a user submits a claim, if we find a match with
# similarity >= 0.85 AND age <= 3 days, we skip web search and use cached verdict.
# Tested on FEVER dataset: 85% paraphrase detection with only 7% false positives.
# Example: "Vaccines cause autism" matches "Vaccines lead to autism in kids" (0.87)
CACHE_HIT_THRESHOLD = 0.85

# Cache freshness: Even high-similarity matches are refreshed via web search if
# older than this. Balances data freshness vs API cost.
# Future: Implement category-based TTL (timeless facts: 30d, current events: 1d)
CACHE_MAX_AGE_DAYS = 3

# Number of similar claims to retrieve for reasoning context
DEFAULT_TOP_K = 10

# Time decay: Recent claims rank higher using Gaussian decay.
# With sigma=90: 1-week-old = 99% weight, 90-day-old = 80%, 1-year = 50%
# Provides smooth degradation while preserving useful historical context.
TIME_DECAY_SIGMA_DAYS = 90

# Dataset Configuration
FEVER_SAMPLE_SIZE = 300
LIAR_SAMPLE_SIZE = 100
SCIFACT_SAMPLE_SIZE = 100

# Verdicts
VERDICT_TRUE = "True"
VERDICT_FALSE = "False"
VERDICT_UNCERTAIN = "Uncertain"

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.7
LOW_CONFIDENCE_THRESHOLD = 0.5


def validate_config():
    """Validate that all required configuration is present."""
    required_vars = [
        ("QDRANT_URL", QDRANT_URL),
        ("QDRANT_API_KEY", QDRANT_API_KEY),
        ("GROQ_API_KEY", GROQ_API_KEY),
    ]
    
    missing = [name for name, value in required_vars if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True


if __name__ == "__main__":
    validate_config()
    print("Configuration validated successfully!")
    print(f"Qdrant URL: {QDRANT_URL}")
    print(f"Collection: {COLLECTION_NAME}")
