"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, ShieldAlert, Cpu, Bot, CheckCircle2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiClient } from "@/lib/api-client";

interface DashboardMetrics {
  claims_processed: number;
  fraud_prevented: number;
  active_agents: number;
  automation_rate: number;
  chart_data: Array<{name: string, claims: number, fraud: number}>;
}

interface LogEvent {
  level: string;
  source: string;
  message: string;
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [tenantCount, setTenantCount] = useState<number | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Fetch metrics
    const fetchMetrics = async () => {
      try {
        const data = await apiClient.get<DashboardMetrics>("/analytics/dashboards", { tenant_id: "default" });
        setMetrics(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch dashboard metrics", err);
        setError("Unable to load dashboard metrics from the server.");
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // refresh every 30s

    const fetchTenants = async () => {
      try {
        const tenants = await apiClient.get<Array<Record<string, unknown>>>("/platform/tenants");
        setTenantCount(tenants.length);
      } catch (err) {
        console.error("Failed to fetch tenant count", err);
      }
    };
    fetchTenants();

    // Connect to WebSocket (non-blocking)
    try {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/api/v1/logs/ws";
      ws.current = new WebSocket(wsUrl);
      ws.current.onmessage = (event) => {
        try {
          const log = JSON.parse(event.data) as LogEvent;
          setLogs(prev => [log, ...prev].slice(0, 50));
        } catch (e) {
          console.error(e);
        }
      };
      ws.current.onerror = () => {
        console.warn("WebSocket connection failed — live logs unavailable");
      };
    } catch {
      console.warn("WebSocket not available");
    }

    return () => {
      clearInterval(interval);
      ws.current?.close();
    };
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-red-600" role="alert">
        {error}
      </div>
    );
  }

  if (!metrics) {
    return <div className="flex items-center justify-center h-64">Loading Enterprise Data...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Executive Dashboard</h1>
        <div className="flex gap-2">
          <span className="inline-flex items-center rounded-md bg-green-500/10 px-2 py-1 text-xs font-medium text-green-500 ring-1 ring-inset ring-green-500/20">
            System Healthy
          </span>
          {tenantCount !== null && (
            <span className="inline-flex items-center rounded-md bg-blue-500/10 px-2 py-1 text-xs font-medium text-blue-500 ring-1 ring-inset ring-blue-500/20">
              {tenantCount} Active Tenant{tenantCount === 1 ? "" : "s"}
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Claims Processed Today</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.claims_processed.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Real-time DB query</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fraud Prevented</CardTitle>
            <ShieldAlert className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${metrics.fraud_prevented.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Estimated savings</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active AI Agents</CardTitle>
            <Bot className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.active_agents}</div>
            <p className="text-xs text-muted-foreground">Across specialized teams</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Automation Rate</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.automation_rate}%</div>
            <p className="text-xs text-muted-foreground">STP Approved</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Processing Volume & Fraud Detection</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.chart_data}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="name" className="text-xs" stroke="hsl(var(--muted-foreground))" />
                  <YAxis className="text-xs" stroke="hsl(var(--muted-foreground))" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                    itemStyle={{ color: 'hsl(var(--foreground))' }}
                  />
                  <Line type="monotone" dataKey="claims" stroke="hsl(var(--primary))" strokeWidth={2} />
                  <Line type="monotone" dataKey="fraud" stroke="hsl(var(--destructive))" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Live Agent Operations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 h-[300px] overflow-y-auto">
              {logs.length === 0 ? (
                 <div className="text-sm text-muted-foreground">Connecting to Pipeline WebSocket...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="flex gap-2 items-start text-sm border-b border-border/50 pb-2">
                    <span className={`font-mono text-xs mt-0.5 px-1 rounded ${log.level === 'WARN' ? 'bg-amber-500/20 text-amber-500' : 'bg-primary/20 text-primary'}`}>
                      {log.level}
                    </span>
                    <div>
                      <div className="font-medium text-muted-foreground">{log.source}</div>
                      <div>{log.message}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
