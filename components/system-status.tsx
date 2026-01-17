"use client"

import { useEffect, useState } from "react"
import { Activity, CheckCircle2, XCircle, ExternalLink, Server, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { checkApiHealth } from "@/lib/api"

export function SystemStatus() {
  const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking")
  const [errorMessage, setErrorMessage] = useState<string>("")

  useEffect(() => {
    const checkStatus = async () => {
      try {
        await checkApiHealth()
        setApiStatus("online")
        setErrorMessage("")
      } catch (error) {
        setApiStatus("offline")
        setErrorMessage(error instanceof Error ? error.message : "Connection failed")
      }
    }

    checkStatus()
    const interval = setInterval(checkStatus, 10000) // Check every 10 seconds

    return () => clearInterval(interval)
  }, [])

  const StatusBadge = ({ status }: { status: typeof apiStatus }) => {
    if (status === "checking") {
      return (
        <Badge className="gap-1.5 bg-blue-100 text-blue-700 border-blue-200">
          <Loader2 className="w-3 h-3 animate-spin" />
          Checking
        </Badge>
      )
    }
    if (status === "online") {
      return (
        <Badge className="gap-1.5 bg-emerald-100 text-emerald-700 border-emerald-200">
          <CheckCircle2 className="w-3 h-3" />
          Operational
        </Badge>
      )
    }
    return (
      <Badge className="gap-1.5 bg-red-100 text-red-700 border-red-200">
        <XCircle className="w-3 h-3" />
        Offline
      </Badge>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card className="border-border shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary" />
            System Status
          </CardTitle>
          <CardDescription>Current operational status of verification services</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* API Status */}
          <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5 text-muted-foreground" />
              <div>
                <h4 className="text-sm font-medium text-foreground">Verification API</h4>
                <p className="text-xs text-muted-foreground">
                  {apiStatus === "online" 
                    ? "Core verification pipeline at localhost:8000" 
                    : apiStatus === "offline"
                    ? errorMessage
                    : "Checking connection..."}
                </p>
              </div>
            </div>
            <StatusBadge status={apiStatus} />
          </div>

          {/* Memory Service */}
          <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5 text-muted-foreground" />
              <div>
                <h4 className="text-sm font-medium text-foreground">Memory Service (Qdrant)</h4>
                <p className="text-xs text-muted-foreground">Vector similarity search backend</p>
              </div>
            </div>
            <StatusBadge status={apiStatus} />
          </div>

          {/* Web Search */}
          <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5 text-muted-foreground" />
              <div>
                <h4 className="text-sm font-medium text-foreground">Web Search (Tavily)</h4>
                <p className="text-xs text-muted-foreground">External verification fallback</p>
              </div>
            </div>
            <StatusBadge status={apiStatus} />
          </div>
        </CardContent>
      </Card>

      {/* API Documentation Link */}
      <Card className="border-border shadow-sm">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-foreground">API Documentation</h4>
              <p className="text-xs text-muted-foreground mt-1">FastAPI interactive documentation</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 bg-transparent"
              onClick={() => window.open("http://localhost:8000/docs", "_blank")}
            >
              View Docs
              <ExternalLink className="w-3.5 h-3.5" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
