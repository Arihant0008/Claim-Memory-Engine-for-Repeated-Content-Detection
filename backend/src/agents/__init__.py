"""
Multi-agent modules for the PCM system.
"""

from .normalizer import ClaimNormalizer
from .retriever import RetrievalAgent
from .reasoner import ReasoningAgent
from .memory import MemoryUpdateAgent

# Web search is optional (requires TAVILY_API_KEY)
try:
    from .web_search import WebSearchAgent
    _web_search_available = True
except ImportError:
    WebSearchAgent = None
    _web_search_available = False

__all__ = [
    "ClaimNormalizer",
    "RetrievalAgent", 
    "ReasoningAgent",
    "MemoryUpdateAgent",
    "WebSearchAgent",
]
