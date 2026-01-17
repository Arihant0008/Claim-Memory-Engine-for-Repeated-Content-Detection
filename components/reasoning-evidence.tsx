"use client"

import { useState } from "react"
import { ChevronDown, ChevronRight, Brain, FileSearch, ExternalLink } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import type { VerificationResult, Evidence } from "@/lib/types"
import { cn } from "@/lib/utils"

interface ReasoningEvidenceProps {
  result: VerificationResult
}

export function ReasoningEvidence({ result }: ReasoningEvidenceProps) {
  const [reasoningOpen, setReasoningOpen] = useState(true)
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null)

  const reliabilityColors = {
    High: "bg-emerald-100 text-emerald-700 border-emerald-200",
    Medium: "bg-amber-100 text-amber-700 border-amber-200",
    Low: "bg-red-100 text-red-700 border-red-200",
  }

  return (
    <Card className="border-border shadow-sm">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-primary" />
          <CardTitle className="text-base font-medium">How the system reached this conclusion</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Reasoning Trace */}
        <Collapsible open={reasoningOpen} onOpenChange={setReasoningOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-3 h-auto bg-muted/50 hover:bg-muted">
              <span className="flex items-center gap-2 text-sm font-medium">
                <FileSearch className="w-4 h-4 text-muted-foreground" />
                Reasoning Trace
              </span>
              {reasoningOpen ? (
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="mt-3 space-y-2 pl-4 border-l-2 border-primary/20">
              {result.reasoning.map((step, index) => (
                <div key={index} className="flex items-start gap-3 py-2">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-medium flex items-center justify-center">
                    {index + 1}
                  </span>
                  <p className="text-sm text-foreground/80 pt-0.5">{step}</p>
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Evidence Table */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
            Evidence List
            <Badge variant="secondary" className="text-xs">
              {result.evidence.length} sources
            </Badge>
          </h4>

          <div className="border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Claim</th>
                    <th className="text-right py-3 px-4 font-medium text-muted-foreground w-24">Similarity</th>
                    <th className="text-right py-3 px-4 font-medium text-muted-foreground w-20">Seen</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground w-28">Source</th>
                    <th className="text-center py-3 px-4 font-medium text-muted-foreground w-24">Reliability</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {result.evidence.map((evidence, index) => (
                    <tr
                      key={index}
                      className={cn(
                        "hover:bg-muted/30 cursor-pointer transition-colors",
                        selectedEvidence === evidence && "bg-primary/5",
                      )}
                      onClick={() => setSelectedEvidence(selectedEvidence === evidence ? null : evidence)}
                    >
                      <td className="py-3 px-4">
                        <span className="line-clamp-1 text-foreground/80">{evidence.claim}</span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-foreground">
                        {(evidence.similarity * 100).toFixed(0)}%
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-foreground">{evidence.seenCount}×</td>
                      <td className="py-3 px-4">
                        <span className="flex items-center gap-1 text-primary">
                          {evidence.source}
                          <ExternalLink className="w-3 h-3" />
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge
                          variant="outline"
                          className={cn("text-xs border", reliabilityColors[evidence.reliability])}
                        >
                          {evidence.reliability}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Expanded Evidence Detail */}
          {selectedEvidence && (
            <div className="p-4 bg-muted/30 rounded-lg border border-border">
              <h5 className="text-sm font-medium text-foreground mb-2">Full Evidence</h5>
              <p className="text-sm text-foreground/80">{selectedEvidence.claim}</p>
              <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
                <span>
                  Source: <strong className="text-foreground">{selectedEvidence.source}</strong>
                </span>
                <span>
                  Similarity:{" "}
                  <strong className="text-foreground font-mono">
                    {(selectedEvidence.similarity * 100).toFixed(1)}%
                  </strong>
                </span>
                <span>
                  Observed: <strong className="text-foreground font-mono">{selectedEvidence.seenCount}</strong> times
                </span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
