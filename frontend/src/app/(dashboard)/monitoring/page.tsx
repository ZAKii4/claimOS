"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, Server, AlertCircle, CheckCircle2, Clock, DollarSign, Database, HardDrive } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface HealthStatus {
  status: string;
  components: string[];
}

interface Metrics {
  counters: Record<string, number>;
  latencies: Record<string, number>;
}

interface CostBreakdown {
  total_by_category: Record<string, number>;
  total_by_claim: Record<string, number>;
  global_total: number;
}

interface Alert {
  id: string;
  severity: string;
  message: string;
  timestamp: string;
}

export default function MonitoringPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [costs, setCosts] = useState<CostBreakdown | null>(null);
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [healthData, metricsData, costsData, alertsData] = await Promise.all([
          apiClient.get<HealthStatus>("/monitoring/health"),
          apiClient.get<Metrics>("/monitoring/metrics"),
          apiClient.get<CostBreakdown>("/monitoring/costs"),
          apiClient.get<Alert[]>("/monitoring/alerts")
        ]);
        
        setHealth(healthData);
        setMetrics(metricsData);
        setCosts(costsData);
        setAlerts(alertsData);
      } catch (err) {
        console.error("Failed to fetch monitoring data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 15000); // refresh every 15s for monitoring
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return <div className="flex items-center justify-center h-64">Loading System Telemetry...</div>;
  }

  const isHealthy = health?.status === "GREEN";

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Monitoring Center</h1>
          <p className="text-muted-foreground mt-1">Real-time system telemetry and infrastructure health.</p>
        </div>
        <div className="flex gap-2">
          {health && (
            <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
              isHealthy 
                ? 'bg-green-500/10 text-green-500 ring-green-500/20' 
                : 'bg-destructive/10 text-destructive ring-destructive/20'
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-destructive animate-pulse'}`} />
              System Status: {health.status}
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts?.length || 0}</div>
            <p className="text-xs text-muted-foreground">Requiring attention</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Infrastructure Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">€{(costs?.global_total || 0).toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">Accumulated LLM/compute</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Components</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{health?.components.length || 0}</div>
            <p className="text-xs text-muted-foreground">Databases & Services</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Metric Counters</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Object.keys(metrics?.counters || {}).length}</div>
            <p className="text-xs text-muted-foreground">Tracked in Prometheus</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>System Telemetry</CardTitle>
            <CardDescription>Real-time latencies and operation counters</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-blue-500" /> API Latencies (ms)
                </h4>
                {metrics && Object.keys(metrics.latencies).length > 0 ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {Object.entries(metrics.latencies).map(([key, val]) => (
                      <div key={key} className="p-3 bg-muted/50 rounded-lg border border-border/50">
                        <div className="text-xs text-muted-foreground truncate" title={key}>{key}</div>
                        <div className="text-lg font-semibold">{val.toFixed(2)} ms</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground italic p-4 bg-muted/20 rounded-lg border border-dashed text-center">
                    No latency metrics recorded yet
                  </div>
                )}
              </div>

              <div>
                <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-green-500" /> Operation Counters
                </h4>
                {metrics && Object.keys(metrics.counters).length > 0 ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {Object.entries(metrics.counters).map(([key, val]) => (
                      <div key={key} className="p-3 bg-muted/50 rounded-lg border border-border/50">
                        <div className="text-xs text-muted-foreground truncate" title={key}>{key}</div>
                        <div className="text-lg font-semibold">{val}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground italic p-4 bg-muted/20 rounded-lg border border-dashed text-center">
                    No counter metrics recorded yet
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1 flex flex-col">
          <CardHeader>
            <CardTitle>Component Health</CardTitle>
            <CardDescription>Backend infrastructure status</CardDescription>
          </CardHeader>
          <CardContent className="flex-1">
            <div className="space-y-4">
              {health?.components.map((component, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg border border-border/50">
                  <div className="flex items-center gap-3">
                    {component === 'postgresql' ? (
                      <Database className="w-4 h-4 text-blue-400" />
                    ) : component === 'neo4j' ? (
                      <HardDrive className="w-4 h-4 text-green-400" />
                    ) : (
                      <Server className="w-4 h-4 text-muted-foreground" />
                    )}
                    <span className="text-sm font-medium capitalize">{component}</span>
                  </div>
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
