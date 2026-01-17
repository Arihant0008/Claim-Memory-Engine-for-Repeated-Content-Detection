import { Globe, ExternalLink } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { WebSearch } from "@/lib/types"

interface WebSearchSectionProps {
  webSearch: WebSearch
}

export function WebSearchSection({ webSearch }: WebSearchSectionProps) {
  return (
    <Card className="border-border shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-primary" />
          <CardTitle className="text-base font-medium">Web Search Results</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Query */}
        <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
          <span className="text-xs font-medium text-muted-foreground">Query:</span>
          <span className="text-sm text-foreground">{webSearch.query}</span>
        </div>

        {/* Direct Answer */}
        {webSearch.directAnswer && (
          <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
            <Badge variant="outline" className="mb-2 text-xs bg-card">
              Direct Answer
            </Badge>
            <p className="text-sm text-foreground">{webSearch.directAnswer}</p>
          </div>
        )}

        {/* Sources */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-foreground">Sources</h4>
          <div className="space-y-2">
            {webSearch.sources.map((source, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-primary">{source.domain}</span>
                    <ExternalLink className="w-3 h-3 text-muted-foreground" />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{source.snippet}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
