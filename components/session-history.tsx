"use client"

import { CheckCircle2, XCircle, HelpCircle, Database, Globe, Clock } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { HistoryItem, Verdict } from "@/lib/types"
import { cn } from "@/lib/utils"

interface SessionHistoryProps {
  history: HistoryItem[]
  onSelect: (item: HistoryItem) => void
}

export function SessionHistory({ history, onSelect }: SessionHistoryProps) {
  const verdictIcons: Record<Verdict, typeof CheckCircle2> = {
    True: CheckCircle2,
    False: XCircle,
    Uncertain: HelpCircle,
  }

  const verdictColors: Record<Verdict, string> = {
    True: "text-emerald-600",
    False: "text-red-600",
    Uncertain: "text-amber-600",
  }

  if (history.length === 0) {
    return (
      <Card className="border-border shadow-sm">
        <CardContent className="p-8">
          <div className="flex flex-col items-center justify-center text-center space-y-3">
            <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center">
              <Clock className="w-7 h-7 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-medium text-foreground">No History Yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm">Your verification history will appear here</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-border shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Session History</CardTitle>
        <CardDescription>
          {history.length} verification{history.length !== 1 ? "s" : ""} in this session
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left py-3 px-4 font-medium text-muted-foreground">Claim</th>
                  <th className="text-center py-3 px-4 font-medium text-muted-foreground w-28">Verdict</th>
                  <th className="text-right py-3 px-4 font-medium text-muted-foreground w-28">Confidence</th>
                  <th className="text-center py-3 px-4 font-medium text-muted-foreground w-32">Source</th>
                  <th className="text-right py-3 px-4 font-medium text-muted-foreground w-32">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {history.map((item) => {
                  const VerdictIcon = verdictIcons[item.verdict]
                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-muted/30 cursor-pointer transition-colors"
                      onClick={() => onSelect(item)}
                    >
                      <td className="py-3 px-4">
                        <span className="line-clamp-1 text-foreground">{item.claim}</span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <VerdictIcon className={cn("w-4 h-4", verdictColors[item.verdict])} />
                          <span className={cn("font-medium", verdictColors[item.verdict])}>{item.verdict}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-foreground">
                        {Math.round(item.confidence * 100)}%
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Badge variant="outline" className="gap-1 text-xs">
                          {item.cacheHit ? (
                            <>
                              <Database className="w-3 h-3" />
                              Memory
                            </>
                          ) : (
                            <>
                              <Globe className="w-3 h-3" />
                              Web
                            </>
                          )}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right text-muted-foreground">
                        {new Date(item.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
