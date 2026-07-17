"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, Terminal, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface AgentInfo {
  name: string;
  version: string;
  capabilities: string[];
}

interface AgentMetric {
  total_calls: number;
  success_rate: number;
  avg_latency_ms: number;
}

interface AgentDisplay {
  id: string;
  name: string;
  version: string;
  capabilities: string[];
  status: string;
  tasks: number;
}

interface LogEvent {
  level: string;
  source: string;
  message: string;
}

export default function AgentsConsolePage() {
  const [agents, setAgents] = useState<AgentDisplay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const [data, metrics] = await Promise.all([
          apiClient.get<Record<string, AgentInfo>>("/agents/"),
          apiClient
            .get<Record<string, AgentMetric>>("/agents/metrics")
            .catch(() => ({} as Record<string, AgentMetric>)),
        ]);
        const agentList: AgentDisplay[] = Object.entries(data).map(([id, info]) => {
          const metric = metrics[id];
          return {
            id,
            name: info.name,
            version: info.version,
            capabilities: info.capabilities,
            status: metric && metric.total_calls > 0 ? "ACTIVE" : "IDLE",
            tasks: metric?.total_calls ?? 0,
          };
        });
        setAgents(agentList);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch agents", err);
        setError("Unable to load the agent registry from the server.");
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();

    // Connect to live logs WebSocket
    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/api/v1/logs/ws";
      ws.current = new WebSocket(wsUrl);
      ws.current.onmessage = (event) => {
        try {
          const log = JSON.parse(event.data) as LogEvent;
          setLogs(prev => [log, ...prev].slice(0, 100));
        } catch { /* ignore parse errors */ }
      };
      ws.current.onerror = () => {
        console.warn("WebSocket connection failed — live logs unavailable");
      };
    } catch {
      console.warn("WebSocket not available");
    }

    return () => { ws.current?.close(); };
  }, []);

  const statusColor = (status: string) => {
    switch (status) {
      case "PROCESSING": return "text-blue-500";
      case "DEBATING": return "text-purple-500";
      case "ACTIVE": return "text-green-500";
      default: return "text-muted-foreground";
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Multi-Agent Live Console</h1>
        <Badge variant="outline" className="text-green-500 border-green-500/20">ACOS Distributed Mode</Badge>
      </div>

      {loading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="text-sm text-red-600 p-4" role="alert">
          {error}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {agents.map((agent) => (
            <Card key={agent.id} className="relative overflow-hidden">
              {agent.status === "PROCESSING" && (
                <div className="absolute top-0 left-0 w-full h-1 bg-blue-500 animate-pulse"></div>
              )}
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                  <Bot className="w-4 h-4" />
                  {agent.name}
                </CardTitle>
                <Badge variant="secondary" className="text-xs">v{agent.version}</Badge>
              </CardHeader>
              <CardContent>
                <div className="mt-2 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Status</span>
                    <span className={statusColor(agent.status)}>
                      {agent.status}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Queue</span>
                    <span>{agent.tasks} tasks</span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {agent.capabilities.map(cap => (
                      <Badge key={cap} variant="outline" className="text-xs">{cap}</Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card className="flex-1 mt-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="w-4 h-4" />
            Live Reasoning Trace
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-black/90 text-green-400 font-mono text-sm p-4 rounded-md h-[400px] overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-muted-foreground">Connecting to agent pipeline WebSocket...</p>
            ) : (
              logs.map((log, i) => (
                <p key={i} className={log.level === "WARN" ? "text-amber-400" : log.level === "ERROR" ? "text-red-400" : ""}>
                  [{log.source}] {log.message}
                </p>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
