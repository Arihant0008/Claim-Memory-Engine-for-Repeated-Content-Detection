import { CheckCircle2, XCircle, HelpCircle, Database, Globe, Loader2, FileText, Eye, RefreshCw } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { VerificationResult } from "@/lib/types"
import { cn } from "@/lib/utils"

interface DecisionZoneProps {
  result: VerificationResult | null
  isVerifying: boolean
}

export function DecisionZone({ result, isVerifying }: DecisionZoneProps) {
  if (isVerifying) {
    return (
      <Card className="border-border shadow-sm overflow-hidden min-h-[320px]">
        <CardContent className="p-10">
          <div className="flex flex-col items-center justify-center text-center space-y-6">
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-accent flex items-center justify-center ring-8 ring-accent/50">
                <Loader2 className="w-10 h-10 text-primary animate-spin" />
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-semibold text-foreground">Analyzing Claim</h3>
              <p className="text-sm text-muted-foreground max-w-md">Running multi-agent verification pipeline...</p>
            </div>
            <div className="flex items-center gap-8 text-xs text-muted-foreground">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                Normalizing
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-muted-foreground/30" />
                Memory Retrieval
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-muted-foreground/30" />
                Reasoning
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!result) {
    return (
      <Card className="border-border shadow-sm border-dashed min-h-[320px]">
        <CardContent className="p-10">
          <div className="flex flex-col items-center justify-center text-center space-y-4 h-full">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <HelpCircle className="w-8 h-8 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-medium text-foreground">No Verification Yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm">Enter a claim on the left to begin verification</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const verdictConfig = {
    True: {
      icon: CheckCircle2,
      bgColor: "bg-emerald-50",
      iconColor: "text-emerald-600",
      badgeColor: "bg-emerald-600 text-white border-emerald-700",
      ringColor: "ring-emerald-200",
      accentBorder: "border-l-emerald-500",
    },
    False: {
      icon: XCircle,
      bgColor: "bg-red-50",
      iconColor: "text-red-600",
      badgeColor: "bg-red-600 text-white border-red-700",
      ringColor: "ring-red-200",
      accentBorder: "border-l-red-500",
    },
    Uncertain: {
      icon: HelpCircle,
      bgColor: "bg-amber-50",
      iconColor: "text-amber-600",
      badgeColor: "bg-amber-500 text-white border-amber-600",
      ringColor: "ring-amber-200",
      accentBorder: "border-l-amber-500",
    },
  }

  const config = verdictConfig[result.verdict]
  const VerdictIcon = config.icon

  return (
    <div className="space-y-4">
      {/* Main Verdict Card - Dominant */}
      <Card className={cn("shadow-md overflow-hidden border-l-4", config.bgColor, config.accentBorder)}>
        <CardContent className="p-8">
          <div className="flex flex-col items-center text-center space-y-6">
            {/* Large Verdict Icon & Badge */}
            <div className="space-y-4">
              <div
                className={cn(
                  "w-24 h-24 rounded-2xl flex items-center justify-center ring-8 mx-auto",
                  config.bgColor,
                  config.ringColor,
                )}
              >
                <VerdictIcon className={cn("w-14 h-14", config.iconColor)} />
              </div>
              <Badge className={cn("text-lg font-bold px-6 py-2 border", config.badgeColor)}>{result.verdict}</Badge>
            </div>

            {/* Confidence - Emphasized */}
            <div className="space-y-1">
              <div className="text-5xl font-bold text-foreground font-mono tracking-tight">
                {Math.round(result.confidence * 100)}%
              </div>
              <p className="text-sm text-muted-foreground uppercase tracking-wide font-medium">Confidence</p>
            </div>

            {/* Source Badge - Memory vs Web */}
            <div>
              {result.cacheHit ? (
                <Badge
                  variant="outline"
                  className="gap-2 px-4 py-2 text-sm bg-accent/50 border-accent text-accent-foreground"
                >
                  <Database className="w-4 h-4" />
                  Answered from Memory
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-2 px-4 py-2 text-sm bg-blue-50 border-blue-200 text-blue-700">
                  <Globe className="w-4 h-4" />
                  Verified via Web Search
                </Badge>
              )}
            </div>

            {/* Explanation */}
            <p className="text-sm text-foreground/80 leading-relaxed max-w-lg">{result.explanation}</p>
          </div>
        </CardContent>
      </Card>

      {/* System Intelligence Strip - Subtle explanation */}
      <Card className="border-border shadow-sm bg-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">System Intelligence</h4>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-4">
            {/* Evidence Count */}
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-muted">
                <FileText className="w-4 h-4 text-foreground" />
              </div>
              <div>
                <div className="text-lg font-bold text-foreground font-mono">{result.evidence.length}</div>
                <p className="text-xs text-muted-foreground">Evidence sources</p>
              </div>
            </div>

            {/* Seen Count */}
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-accent">
                <Eye className="w-4 h-4 text-accent-foreground" />
              </div>
              <div>
                <div className="text-lg font-bold text-foreground font-mono">{result.seenCount}×</div>
                <p className="text-xs text-muted-foreground">Times observed</p>
              </div>
            </div>

            {/* Memory Status */}
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "p-2 rounded-lg",
                  result.memoryUpdate === "updated"
                    ? "bg-primary/10"
                    : result.memoryUpdate === "created"
                      ? "bg-emerald-100"
                      : "bg-muted",
                )}
              >
                <RefreshCw
                  className={cn(
                    "w-4 h-4",
                    result.memoryUpdate === "updated"
                      ? "text-primary"
                      : result.memoryUpdate === "created"
                        ? "text-emerald-600"
                        : "text-muted-foreground",
                  )}
                />
              </div>
              <div>
                <div className="text-sm font-semibold text-foreground capitalize">{result.memoryUpdate}</div>
                <p className="text-xs text-muted-foreground">Memory status</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
