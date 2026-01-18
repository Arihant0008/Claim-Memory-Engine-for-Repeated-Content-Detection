"""
Web Search Agent using Tavily API
Searches the internet for fact-checking and verification.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


@dataclass
class WebSearchResult:
    """Represents a single search result."""
    title: str
    url: str
    content: str
    score: float
    published_date: Optional[str] = None


@dataclass
class WebSearchResponse:
    """Complete web search response."""
    query: str
    results: list[WebSearchResult]
    answer: Optional[str]  # Tavily can provide a direct answer
    search_time: float
    sources_count: int


class WebSearchAgent:
    """
    Agent for searching the internet using Tavily API.
    Tavily is optimized for AI agents and fact-checking.
    
    Features:
    - Searches multiple sources at once
    - Provides relevance scores
    - Can include/exclude domains
    - Optimized for factual queries
    """
    
    def __init__(self):
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY not found in environment")
        
        # Import tavily here to avoid import errors if not installed
        try:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=TAVILY_API_KEY)
        except ImportError:
            raise ImportError("Please install tavily-python: pip install tavily-python")
    
    def search(
        self,
        query: str,
        search_depth: str = "basic",  # "basic" or "advanced"
        max_results: int = 5,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None
    ) -> WebSearchResponse:
        """
        Search the internet for information about a claim.
        
        Args:
            query: The search query (claim to verify)
            search_depth: "basic" (faster) or "advanced" (more thorough)
            max_results: Maximum number of results to return
            include_domains: Only search these domains (optional)
            exclude_domains: Exclude these domains (optional)
            
        Returns:
            WebSearchResponse with search results
        """
        start_time = datetime.now()
        
        # Default domains for fact-checking
        if include_domains is None:
            include_domains = []  # Search all by default
        
        if exclude_domains is None:
            # Exclude unreliable sources
            exclude_domains = [
                "reddit.com",
                "twitter.com",
                "facebook.com",
                "tiktok.com"
            ]
        
        try:
            # Perform the search
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=include_domains if include_domains else None,
                exclude_domains=exclude_domains
            )
            
            # Parse results
            results = []
            for item in response.get("results", []):
                results.append(WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    score=item.get("score", 0.0),
                    published_date=item.get("published_date")
                ))
            
            search_time = (datetime.now() - start_time).total_seconds()
            
            return WebSearchResponse(
                query=query,
                results=results,
                answer=response.get("answer"),  # Direct answer if available
                search_time=search_time,
                sources_count=len(results)
            )
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            # Return empty result on error
            return WebSearchResponse(
                query=query,
                results=[],
                answer=None,
                search_time=0,
                sources_count=0
            )
    
    def search_for_fact_check(self, claim: str) -> WebSearchResponse:
        """
        Specialized search for fact-checking a claim.
        Adds fact-check context and current date to the query.
        
        Args:
            claim: The claim to fact-check
            
        Returns:
            WebSearchResponse focused on fact-checking sources
        """
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().strftime("%B")
        
        # Enhance query for fact-checking with current date context
        # This helps get more recent/relevant results for time-sensitive claims
        enhanced_query = f"fact check {current_year}: {claim}"
        
        # Prioritize fact-checking websites
        fact_check_domains = [
            "snopes.com",
            "politifact.com",
            "factcheck.org",
            "reuters.com/fact-check",
            "apnews.com",
            "bbc.com"
        ]
        
        return self.search(
            query=enhanced_query,
            search_depth="advanced",  # More thorough for fact-checking
            max_results=5,
            include_domains=[]  # Search all, but fact-check query helps
        )
    
    def format_for_llm(self, response: WebSearchResponse) -> str:
        """
        Format search results for LLM consumption.
        
        Args:
            response: The search response to format
            
        Returns:
            Formatted string for LLM context
        """
        if not response.results:
            return "No web search results found for this claim."
        
        formatted = [f"Web Search Results for: \"{response.query}\"\n"]
        formatted.append(f"Found {response.sources_count} sources:\n")
        
        for i, result in enumerate(response.results, 1):
            formatted.append(f"\n--- Source {i} ---")
            formatted.append(f"Title: {result.title}")
            formatted.append(f"URL: {result.url}")
            formatted.append(f"Relevance: {result.score:.2f}")
            if result.published_date:
                formatted.append(f"Date: {result.published_date}")
            formatted.append(f"Content: {result.content[:500]}...")
        
        if response.answer:
            formatted.append(f"\n--- Direct Answer ---")
            formatted.append(response.answer)
        
        return "\n".join(formatted)


if __name__ == "__main__":
    # Test the web search agent
    agent = WebSearchAgent()
    
    test_claims = [
        "Donald Trump is the current US president",
        "COVID-19 vaccines contain microchips",
        "The Earth is flat"
    ]
    
    for claim in test_claims:
        print(f"\n{'='*60}")
        print(f"Searching: {claim}")
        print("="*60)
        
        result = agent.search_for_fact_check(claim)
        
        print(f"Found {result.sources_count} sources in {result.search_time:.2f}s")
        if result.answer:
            print(f"Direct answer: {result.answer}")
        
        for i, r in enumerate(result.results[:3], 1):
            print(f"\n{i}. {r.title}")
            print(f"   {r.url}")
            print(f"   {r.content[:100]}...")
