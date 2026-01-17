"use client"

import { Shield, History, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"

interface HeaderProps {
  activeView: "verification" | "history" | "status"
  onViewChange: (view: "verification" | "history" | "status") => void
}

export function Header({ activeView, onViewChange }: HeaderProps) {
  return (
    <header className="border-b border-border bg-card">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-primary/10">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground tracking-tight">Mnemonic</h1>
              <p className="text-xs text-muted-foreground -mt-0.5">Persistent Claim Memory for Misinformation Analysis</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            <Button
              variant={activeView === "verification" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => onViewChange("verification")}
              className="gap-2"
            >
              <Shield className="w-4 h-4" />
              <span className="hidden sm:inline">Verify</span>
            </Button>
            <Button
              variant={activeView === "history" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => onViewChange("history")}
              className="gap-2"
            >
              <History className="w-4 h-4" />
              <span className="hidden sm:inline">History</span>
            </Button>
            <Button
              variant={activeView === "status" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => onViewChange("status")}
              className="gap-2"
            >
              <Activity className="w-4 h-4" />
              <span className="hidden sm:inline">Status</span>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  )
}
