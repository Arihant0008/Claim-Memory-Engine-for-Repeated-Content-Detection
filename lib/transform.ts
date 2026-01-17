/**
 * Transforms backend API responses to frontend types
 */

import type { BackendVerificationResponse } from "./api"
import type { VerificationResult, Evidence, WebSearch } from "./types"

/**
 * Map source reliability (0-1) to categorical level
 */
function mapReliability(reliability: number): "High" | "Medium" | "Low" {
  if (reliability >= 0.8) return "High"
  if (reliability >= 0.5) return "Medium"
  return "Low"
}

/**
 * Extract domain from URL
 */
function extractDomain(url: string): string {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname.replace("www.", "")
  } catch {
    return url
  }
}

/**
 * Parse reasoning trace into array of steps
 */
function parseReasoningTrace(trace: string): string[] {
  if (!trace) return []
  
  // Split by newlines and bullet points
  const lines = trace
    .split(/\n+/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => line.replace(/^[•\-\*]\s*/, "").trim())
    .filter((line) => line.length > 0)
  
  // If we got nothing, try splitting by periods
  if (lines.length === 0) {
    return trace
      .split(/\.\s+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 10) // Filter out very short fragments
  }
  
  return lines
}

/**
 * Transform backend response to frontend VerificationResult
 */
export function transformVerificationResponse(
  backendResponse: BackendVerificationResponse,
  originalClaim: string
): VerificationResult {
  const verificationResult = backendResponse.verification_result
  const retrievedEvidence = backendResponse.retrieved_evidence || []
  const webSearchResults = backendResponse.web_search_results

  // Map evidence
  const evidence: Evidence[] = retrievedEvidence.slice(0, 5).map((item) => ({
    claim: item.claim_text,
    similarity: item.similarity_score,
    seenCount: item.seen_count,
    source: item.source,
    reliability: mapReliability(item.source_reliability),
  }))

  // Map web search if present
  let webSearch: WebSearch | null = null
  if (webSearchResults && webSearchResults.sources.length > 0) {
    webSearch = {
      query: webSearchResults.query,
      directAnswer: webSearchResults.answer || undefined,
      sources: webSearchResults.sources.map((source) => ({
        domain: extractDomain(source.url),
        snippet: source.content,
        url: source.url,
      })),
    }
  }

  // Determine memory update action
  let memoryUpdate: "created" | "updated" | "skipped" = "skipped"
  if (backendResponse.seen_count === 1) {
    memoryUpdate = "created"
  } else if (backendResponse.seen_count > 1) {
    memoryUpdate = "updated"
  }

  // Parse reasoning trace
  const reasoningSteps = verificationResult
    ? parseReasoningTrace(verificationResult.reasoning_trace)
    : []

  return {
    id: crypto.randomUUID(),
    claim: originalClaim,
    verdict: verificationResult?.verdict || "Uncertain",
    confidence: verificationResult?.confidence || 0,
    explanation: verificationResult?.explanation || "No explanation available",
    reasoning: reasoningSteps.length > 0 
      ? reasoningSteps 
      : [verificationResult?.evidence_summary || "Processing claim..."],
    evidence,
    cacheHit: backendResponse.cache_hit,
    memoryUpdate,
    seenCount: backendResponse.seen_count,
    timestamp: backendResponse.timestamp,
    webSearch,
    warnings: [],
  }
}
