export type Verdict = "True" | "False" | "Uncertain"

export interface Evidence {
  claim: string
  similarity: number
  seenCount: number
  source: string
  reliability: "High" | "Medium" | "Low"
}

export interface WebSearch {
  query: string
  directAnswer?: string
  sources: {
    domain: string
    snippet: string
    url: string
  }[]
}

export interface VerificationResult {
  id: string
  claim: string
  verdict: Verdict
  confidence: number
  explanation: string
  reasoning: string[]
  evidence: Evidence[]
  cacheHit: boolean
  memoryUpdate: "created" | "updated" | "skipped"
  seenCount: number
  timestamp: string
  webSearch: WebSearch | null
  warnings: string[]
}

export type HistoryItem = VerificationResult
