"use client"

import { useState } from "react"
import { AlertTriangle, ChevronDown, ChevronRight } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Button } from "@/components/ui/button"

interface WarningsErrorsProps {
  warnings: string[]
}

export function WarningsErrors({ warnings }: WarningsErrorsProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (warnings.length === 0) return null

  return (
    <Card className="border-border shadow-sm border-amber-200 bg-amber-50/30">
      <CardContent className="p-0">
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-4 h-auto hover:bg-amber-100/50">
              <span className="flex items-center gap-2 text-sm font-medium text-amber-700">
                <AlertTriangle className="w-4 h-4" />
                {warnings.length} Warning{warnings.length !== 1 ? "s" : ""}
              </span>
              {isOpen ? (
                <ChevronDown className="w-4 h-4 text-amber-600" />
              ) : (
                <ChevronRight className="w-4 h-4 text-amber-600" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="px-4 pb-4 space-y-2">
              {warnings.map((warning, index) => (
                <div key={index} className="p-3 bg-amber-100/50 rounded-lg">
                  <p className="text-xs text-amber-800 font-mono">{warning}</p>
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
