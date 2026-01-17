/**
 * API client for Mnemonic backend
 * Connects to FastAPI server at localhost:8000
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface BackendVerificationResponse {
  normalized_claim: string | null
  cache_hit: boolean
  verification_result: {
    claim_text: string
    normalized_claim: string
    verdict: "True" | "False" | "Uncertain"
    confidence: number
    explanation: string
    evidence_ids: string[]
    evidence_summary: string
    reasoning_trace: string
    web_search_used: boolean
  } | null
  retrieved_evidence: Array<{
    id: string
    claim_text: string
    verdict: "True" | "False" | "Uncertain"
    confidence: number
    source: string
    source_reliability: number
    similarity_score: number
    time_decayed_score: number
    seen_count: number
    timestamp: string
  }> | null
  web_search_results: {
    query: string
    answer: string | null
    search_time: number
    sources: Array<{
      title: string
      url: string
      content: string
      score: number
    }>
  } | null
  web_search_used: boolean
  seen_count: number
  timestamp: string
}

export interface ApiHealthResponse {
  message: string
  status: string
}

/**
 * Check if API is online
 */
export async function checkApiHealth(): Promise<ApiHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/`)
  if (!response.ok) {
    throw new Error(`API health check failed: ${response.statusText}`)
  }
  return response.json()
}

/**
 * Verify a claim through the backend pipeline
 */
export async function verifyClaim(claimText: string): Promise<BackendVerificationResponse> {
  const response = await fetch(`${API_BASE_URL}/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      raw_text: claimText,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `Verification failed: ${response.statusText}`)
  }

  return response.json()
}
