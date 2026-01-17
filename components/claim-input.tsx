"use client"

import { useState } from "react"
import { Send, Loader2, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

interface ClaimInputProps {
  onVerify: (claim: string) => void
  isVerifying: boolean
  hasResult?: boolean
}

export function ClaimInput({ onVerify, isVerifying, hasResult }: ClaimInputProps) {
  const [claim, setClaim] = useState("")

  const handleSubmit = () => {
    if (claim.trim() && !isVerifying) {
      onVerify(claim.trim())
    }
  }

  return (
    <Card className={cn("border-border shadow-sm transition-all duration-300", hasResult && "opacity-90")}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <CardTitle className="text-base font-medium">Enter Claim</CardTitle>
        </div>
        <CardDescription className="text-sm">Submit a statement to verify its accuracy</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          placeholder="Enter a claim to verify (e.g., Vaccines cause autism)"
          value={claim}
          onChange={(e) => setClaim(e.target.value)}
          className={cn(
            "min-h-[100px] resize-none border-border focus:bg-card transition-colors",
            hasResult ? "bg-muted/30" : "bg-muted/50",
          )}
          disabled={isVerifying}
        />
        <Button
          onClick={handleSubmit}
          disabled={!claim.trim() || isVerifying}
          className="w-full gap-2 bg-primary hover:bg-primary/90 font-medium"
        >
          {isVerifying ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Verifying...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Verify Claim
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
