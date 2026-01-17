"use client"

import { useState } from "react"
import { Header } from "@/components/header"
import { ClaimInput } from "@/components/claim-input"
import { DecisionZone } from "@/components/decision-zone"
import { ReasoningEvidence } from "@/components/reasoning-evidence"
import { WebSearchSection } from "@/components/web-search-section"
import { SessionHistory } from "@/components/session-history"
import { SystemStatus } from "@/components/system-status"
import { WarningsErrors } from "@/components/warnings-errors"
import type { VerificationResult, HistoryItem } from "@/lib/types"
import { verifyClaim } from "@/lib/api"
import { transformVerificationResponse } from "@/lib/transform"
import { useToast } from "@/hooks/use-toast"

export default function ClaimVerificationDashboard() {
  const [currentResult, setCurrentResult] = useState<VerificationResult | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeView, setActiveView] = useState<"verification" | "history" | "status">("verification")
  const { toast } = useToast()

  const handleVerify = async (claim: string) => {
    setIsVerifying(true)
    
    try {
      // Call real backend API
      const backendResponse = await verifyClaim(claim)
      
      // Transform backend response to frontend format
      const result = transformVerificationResponse(backendResponse, claim)
      
      setCurrentResult(result)
      setHistory((prev) => [{ ...result, timestamp: new Date().toISOString() }, ...prev])
      
      // Show success toast for cache hits
      if (result.cacheHit) {
        toast({
          title: "Cache Hit",
          description: `Found similar claim in memory (seen ${result.seenCount}x)`,
          duration: 3000,
        })
      }
    } catch (error) {
      // Handle errors
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred"
      
      const errorResult: VerificationResult = {
        id: crypto.randomUUID(),
        claim,
        verdict: "Uncertain",
        confidence: 0,
        explanation: `Verification failed: ${errorMessage}`,
        reasoning: ["Error connecting to verification service"],
        evidence: [],
        cacheHit: false,
        memoryUpdate: "skipped",
        seenCount: 0,
        timestamp: new Date().toISOString(),
        webSearch: null,
        warnings: [errorMessage],
      }
      
      setCurrentResult(errorResult)
      
      toast({
        title: "Verification Error",
        description: errorMessage,
        variant: "destructive",
        duration: 5000,
      })
    } finally {
      setIsVerifying(false)
    }
  }

  const handleSelectHistory = (item: HistoryItem) => {
    setCurrentResult(item)
    setActiveView("verification")
  }

  return (
    <div className="min-h-screen bg-background">
      <Header activeView={activeView} onViewChange={setActiveView} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeView === "verification" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column - Input (Secondary after submission) */}
            <div className={`lg:col-span-4 space-y-6 ${currentResult ? "lg:order-1" : "lg:order-1"}`}>
              <ClaimInput onVerify={handleVerify} isVerifying={isVerifying} hasResult={!!currentResult} />
              {currentResult?.warnings && currentResult.warnings.length > 0 && (
                <WarningsErrors warnings={currentResult.warnings} />
              )}
            </div>

            {/* Right Column - Decision Zone (Primary - Dominant) */}
            <div className="lg:col-span-8 space-y-6 lg:order-2">
              <DecisionZone result={currentResult} isVerifying={isVerifying} />
              {currentResult && (
                <>
                  <ReasoningEvidence result={currentResult} />
                  {currentResult.webSearch && <WebSearchSection webSearch={currentResult.webSearch} />}
                </>
              )}
            </div>
          </div>
        )}

        {activeView === "history" && <SessionHistory history={history} onSelect={handleSelectHistory} />}

        {activeView === "status" && <SystemStatus />}
      </main>
    </div>
  )
}
