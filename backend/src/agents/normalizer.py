"""
Claim Normalizer Agent
Extracts and normalizes claims from raw input (text or images).
"""

import json
import re
import logging
from typing import Optional
from dataclasses import dataclass, asdict

from groq import Groq

from ..config import GROQ_API_KEY, GROQ_MODEL
from ..validation import sanitize_claim_text, escape_html_content

logger = logging.getLogger(__name__)


@dataclass
class NormalizedClaim:
    """Structured representation of a normalized claim."""
    original_text: str
    normalized_text: str
    entities: list[str]
    temporal_markers: Optional[str] = None
    source_type: str = "text"  # text, image, both
    image_description: Optional[str] = None


class ClaimNormalizer:
    """
    Agent 1: Claim Normalizer
    Extracts canonical claims from noisy input using LLM.
    Handles both text and image inputs.
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
    
    def normalize_text(self, raw_text: str) -> NormalizedClaim:
        """
        Normalize a text claim using Groq Llama.
        
        Args:
            raw_text: The raw claim text to normalize
            
        Returns:
            NormalizedClaim with extracted information
        """
        # SECURITY: Sanitize input to prevent prompt injection
        sanitized_text = sanitize_claim_text(raw_text)
        
        prompt = f"""You are a claim extraction expert. Extract the core factual claim from this text.

Text: "{sanitized_text}"

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{"normalized": "the core factual claim in simple present tense", "entities": ["list", "of", "key", "entities"], "temporal": "any time reference or null"}}

Rules:
1. Remove opinions, qualifiers, and hedging language
2. Preserve the factual assertion
3. Extract named entities (people, places, organizations, concepts)
4. Identify any temporal markers (dates, time periods)"""

        try:
            response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up potential markdown formatting
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            
            result = json.loads(result_text)
            
            return NormalizedClaim(
                original_text=raw_text,
                normalized_text=result.get("normalized", raw_text),
                entities=result.get("entities", []),
                temporal_markers=result.get("temporal"),
                source_type="text"
            )
            
        except json.JSONDecodeError as e:
            # Fallback: return original with basic processing
            logger.warning(f"JSON parse error: {e}. Using fallback normalization.")
            return NormalizedClaim(
                original_text=raw_text,
                normalized_text=raw_text.strip(),
                entities=[],
                temporal_markers=None,
                source_type="text"
            )
        except Exception as e:
            logger.error(f"Normalization error: {e}")
            return NormalizedClaim(
                original_text=raw_text,
                normalized_text=raw_text.strip(),
                entities=[],
                temporal_markers=None,
                source_type="text"
            )
    
    def extract_from_image(self, image_path: str) -> NormalizedClaim:
        """
        Image processing not supported (Gemini removed).
        
        Args:
            image_path: Path to the image file
            
        Returns:
            NormalizedClaim with error message
        """
        return NormalizedClaim(
            original_text="",
            normalized_text="",
            entities=[],
            source_type="image",
            image_description="Image processing not supported (Gemini API removed)"
        )
    
    def process(self, text: Optional[str] = None, image_path: Optional[str] = None) -> NormalizedClaim:
        """
        Process input (text, image, or both) to extract normalized claim.
        
        Args:
            text: Optional text input
            image_path: Optional path to image file
            
        Returns:
            NormalizedClaim combining all inputs
        """
        claims = []
        
        if image_path:
            image_claim = self.extract_from_image(image_path)
            claims.append(image_claim)
        
        if text:
            text_claim = self.normalize_text(text)
            claims.append(text_claim)
        
        if not claims:
            raise ValueError("Either text or image_path must be provided")
        
        # Combine claims if both present
        if len(claims) == 2:
            return NormalizedClaim(
                original_text=f"{claims[0].original_text}\n{claims[1].original_text}".strip(),
                normalized_text=claims[1].normalized_text or claims[0].normalized_text,
                entities=list(set(claims[0].entities + claims[1].entities)),
                temporal_markers=claims[1].temporal_markers or claims[0].temporal_markers,
                source_type="both",
                image_description=claims[0].image_description
            )
        
        return claims[0]
    
    def to_dict(self, claim: NormalizedClaim) -> dict:
        """Convert NormalizedClaim to dictionary."""
        return asdict(claim)


if __name__ == "__main__":
    # Test the normalizer
    normalizer = ClaimNormalizer()
    
    test_claims = [
        "They say vaccines might cause autism in children according to some studies",
        "5G towers are spreading COVID-19 coronavirus!",
        "Climate change is just a natural cycle, nothing to worry about",
    ]
    
    for claim in test_claims:
        result = normalizer.normalize_text(claim)
        print(f"\nOriginal: {claim}")
        print(f"Normalized: {result.normalized_text}")
        print(f"Entities: {result.entities}")
