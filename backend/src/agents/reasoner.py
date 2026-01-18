"""
Reasoning Agent
Analyzes claims using retrieved evidence to produce verdicts.
Uses chain-of-thought reasoning with LLM.
"""

import json
import re
import logging
from typing import Optional
from dataclasses import dataclass

from groq import Groq

from ..config import (
    GROQ_API_KEY, GROQ_MODEL,
    VERDICT_TRUE, VERDICT_FALSE, VERDICT_UNCERTAIN,
    HIGH_CONFIDENCE_THRESHOLD, LOW_CONFIDENCE_THRESHOLD
)
from .retriever import RetrievedClaim

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of claim verification."""
    claim_text: str
    normalized_claim: str
    verdict: str
    confidence: float
    explanation: str
    evidence_ids: list[str]
    evidence_summary: str
    reasoning_trace: str


class ReasoningAgent:
    """
    Agent 3: Reasoning Agent
    Uses LLM with chain-of-thought reasoning to assess claim veracity.
    Incorporates retrieved evidence for context-aware verdicts.
    """
    
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
    
    def _format_evidence(self, evidence: list[RetrievedClaim]) -> str:
        """Format evidence for the LLM prompt."""
        if not evidence:
            return "No relevant evidence found in memory."
        
        formatted = []
        for i, ev in enumerate(evidence, 1):
            formatted.append(
                f"{i}. CLAIM: \"{ev.claim_text}\"\n"
                f"   VERDICT: {ev.verdict} (Confidence: {ev.confidence:.0%})\n"
                f"   SOURCE: {ev.source} (Reliability: {ev.source_reliability:.0%})\n"
                f"   SIMILARITY: {ev.similarity_score:.2f}\n"
                f"   SEEN: {ev.seen_count} times"
            )
        
        return "\n".join(formatted)
    
    def _calculate_consensus_confidence(
        self,
        evidence: list[RetrievedClaim],
        predicted_verdict: str
    ) -> float:
        """
        Calculate confidence based on evidence consensus.
        Higher agreement among sources = higher confidence.
        """
        if not evidence:
            return LOW_CONFIDENCE_THRESHOLD
        
        # Count verdicts weighted by reliability and similarity
        verdict_scores = {VERDICT_TRUE: 0, VERDICT_FALSE: 0, VERDICT_UNCERTAIN: 0}
        total_weight = 0
        
        for ev in evidence:
            weight = ev.source_reliability * ev.similarity_score
            verdict_scores[ev.verdict] = verdict_scores.get(ev.verdict, 0) + weight
            total_weight += weight
        
        if total_weight == 0:
            return LOW_CONFIDENCE_THRESHOLD
        
        # Calculate agreement ratio for predicted verdict
        agreement_ratio = verdict_scores.get(predicted_verdict, 0) / total_weight
        
        # Scale to confidence range [0.4, 0.98]
        confidence = 0.4 + (agreement_ratio * 0.58)
        
        return min(confidence, 0.98)
    
    def reason(
        self,
        claim_text: str,
        normalized_claim: str,
        evidence: list[RetrievedClaim],
        use_chain_of_thought: bool = True,
        web_context: Optional[str] = None
    ) -> VerificationResult:
        """
        Reason about a claim using retrieved evidence and optional web search results.
        
        Args:
            claim_text: Original claim text
            normalized_claim: Normalized version of the claim
            evidence: List of retrieved similar claims from memory
            use_chain_of_thought: Whether to use explicit reasoning steps
            web_context: Optional web search results to incorporate
            
        Returns:
            VerificationResult with verdict and explanation
        """
        evidence_text = self._format_evidence(evidence)
        
        # Add web search context if available
        web_section = ""
        if web_context:
            web_section = f"""

LIVE WEB SEARCH RESULTS:
{web_context}

IMPORTANT: Web search results are from live internet sources. Prioritize these for current events and recent claims.
"""
        else:
            web_section = "\nLIVE WEB SEARCH RESULTS: [NONE - Web search was not performed or returned no results]\n"
        
        # Get current date for time-sensitive claims
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        
        if use_chain_of_thought:
            prompt = f"""You are a fact-verification reasoning engine.

CRITICAL RULES (MUST FOLLOW):
1. NEVER expose internal reasoning, chain-of-thought, voting logic, thresholds, weights, or fallback mechanisms.
2. NEVER output fields such as "reasoning_trace", "internal_steps", "weighted_vote", or similar.
3. Your task is to internally reason, then produce a SHORT, USER-SAFE explanation.

FACT VERIFICATION RULES:
1. Verify claims based on authoritative sources first (government, official records, encyclopedic references).
2. For political roles (e.g., President, Prime Minister), you MUST consider time context.
3. If the claim depends on the current date and the date is unclear or conflicting, return "Uncertain".

TIME CONTEXT:
- Current verification date: {current_date}
- Political leadership claims MUST be accurate for this date.

CLAIM TO VERIFY:
"{normalized_claim}"

EVIDENCE FROM MEMORY DATABASE:
{evidence_text}
{web_section}
EVIDENCE HANDLING:
- Use web search results and memory database internally.
- Similarity scores are for internal use ONLY.
- Irrelevant or weakly related claims MUST NOT influence verdicts.

OUTPUT FORMAT (STRICT):
Return ONLY the following JSON structure:

{{
  "verdict": "True | False | Uncertain",
  "confidence": 0.0-1.0,
  "explanation": "One or two sentences explaining the verdict in plain language.",
  "cited_ids": ["relevant source IDs if available"]
}}

DO NOT include:
- Step-by-step reasoning
- Internal votes
- Similarity percentages
- Model decisions
- Fallback descriptions

CRITICAL VERDICT RULES:
- "True" = The claim as stated IS FACTUALLY CORRECT
- "False" = The claim as stated IS FACTUALLY INCORRECT (misinformation)
- "Uncertain" = Not enough evidence to determine

If the claim is false but commonly misunderstood, clearly state the correct fact."""
        else:
            prompt = f"""You are a fact-verification engine. Current date: {current_date}

CLAIM: "{normalized_claim}"

EVIDENCE:
{evidence_text}
{web_section}
Return ONLY JSON with user-safe explanation (no internal reasoning):
{{"verdict": "True/False/Uncertain", "confidence": 0.0-1.0, "explanation": "clear, brief justification"}}"""

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up markdown formatting
            result_text = re.sub(r'^```json\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
            
            result = json.loads(result_text)
            
            # Validate verdict
            verdict = result.get("verdict", VERDICT_UNCERTAIN)
            if verdict not in [VERDICT_TRUE, VERDICT_FALSE, VERDICT_UNCERTAIN]:
                verdict = VERDICT_UNCERTAIN
            
            # Get or calculate confidence
            confidence = float(result.get("confidence", 0.5))
            if confidence <= 0.01 or confidence > 1:
                confidence = self._calculate_consensus_confidence(evidence, verdict)
            
            # Extract cited evidence IDs
            cited_ids = result.get("cited_ids", [])
            if not cited_ids:
                cited_ids = [ev.id for ev in evidence[:3]]  # Default to top 3
            
            # Remove internal reasoning from output - only keep user-safe fields
            reasoning_trace = ""  # No longer exposed to users
            
            return VerificationResult(
                claim_text=claim_text,
                normalized_claim=normalized_claim,
                verdict=verdict,
                confidence=confidence,
                explanation=result.get("explanation", "No explanation provided"),
                evidence_ids=cited_ids,
                evidence_summary=self._create_evidence_summary(evidence, verdict),
                reasoning_trace=reasoning_trace  # Empty - internal use only
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error in reasoning: {e}")
            # Fallback to heuristic-based verdict
            return self._fallback_reasoning(claim_text, normalized_claim, evidence)
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            return self._fallback_reasoning(claim_text, normalized_claim, evidence)
    
    def _fallback_reasoning(
        self,
        claim_text: str,
        normalized_claim: str,
        evidence: list[RetrievedClaim]
    ) -> VerificationResult:
        """
        Fallback reasoning when LLM fails.
        Uses simple voting based on evidence verdicts.
        """
        if not evidence:
            return VerificationResult(
                claim_text=claim_text,
                normalized_claim=normalized_claim,
                verdict=VERDICT_UNCERTAIN,
                confidence=0.3,
                explanation="Insufficient evidence in database",
                evidence_ids=[],
                evidence_summary="No relevant claims found",
                reasoning_trace="Fallback: No evidence available"
            )
        
        # Simple weighted voting
        votes = {VERDICT_TRUE: 0, VERDICT_FALSE: 0, VERDICT_UNCERTAIN: 0}
        
        for ev in evidence:
            weight = ev.similarity_score * ev.source_reliability
            votes[ev.verdict] = votes.get(ev.verdict, 0) + weight
        
        # Find winning verdict
        verdict = max(votes, key=votes.get)
        confidence = self._calculate_consensus_confidence(evidence, verdict)
        
        return VerificationResult(
            claim_text=claim_text,
            normalized_claim=normalized_claim,
            verdict=verdict,
            confidence=confidence,
            explanation=f"Based on {len(evidence)} similar claims in database",
            evidence_ids=[ev.id for ev in evidence[:3]],
            evidence_summary=self._create_evidence_summary(evidence, verdict),
            reasoning_trace="Fallback: Used weighted voting from evidence"
        )
    
    def _create_evidence_summary(
        self,
        evidence: list[RetrievedClaim],
        verdict: str
    ) -> str:
        """Create a human-readable summary of the evidence."""
        if not evidence:
            return "No evidence found in memory."
        
        # Count verdicts
        verdict_counts = {}
        for ev in evidence:
            verdict_counts[ev.verdict] = verdict_counts.get(ev.verdict, 0) + 1
        
        # Get unique sources
        sources = list(set(ev.source for ev in evidence))[:3]
        
        summary_parts = [
            f"Analyzed {len(evidence)} similar claims.",
            f"Verdict distribution: {', '.join(f'{k}: {v}' for k, v in verdict_counts.items())}.",
            f"Sources: {', '.join(sources)}."
        ]
        
        if evidence[0].seen_count > 1:
            summary_parts.append(
                f"Most similar claim seen {evidence[0].seen_count} times previously."
            )
        
        return " ".join(summary_parts)
    
    def assess_confidence_level(self, result: VerificationResult) -> str:
        """
        Provide a human-readable confidence assessment.
        """
        if result.confidence >= HIGH_CONFIDENCE_THRESHOLD:
            return "HIGH - Strong evidence consensus"
        elif result.confidence >= LOW_CONFIDENCE_THRESHOLD:
            return "MEDIUM - Moderate evidence support"
        else:
            return "LOW - Limited or conflicting evidence"


if __name__ == "__main__":
    from .retriever import RetrievalAgent
    
    # Test the reasoning agent
    retriever = RetrievalAgent()
    reasoner = ReasoningAgent()
    
    test_claim = "Vaccines cause autism in children"
    
    # Get evidence
    evidence = retriever.search(test_claim, k=5)
    
    # Reason about the claim
    result = reasoner.reason(
        claim_text=test_claim,
        normalized_claim=test_claim,
        evidence=evidence
    )
    
    print(f"\nClaim: {result.claim_text}")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Explanation: {result.explanation}")
    print(f"\nReasoning: {result.reasoning_trace}")
