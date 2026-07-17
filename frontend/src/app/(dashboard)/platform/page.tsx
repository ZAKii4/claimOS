"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Server, ShieldCheck, Activity, Database, AlertTriangle, ArrowUpCircle, RefreshCw } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface SystemHealth {
  status: string;
  components: string[];
}

const incidents = [
  { id: "INC-901", title: "High LLM Latency", severity: "Medium", status: "RESOLVED", time: "1h ago" },
  { id: "INC-902", title: "Ollama Worker OOM", severity: "High", status: "OPEN", time: "5m ago" },
];

const releases = [
  { version: "v2.5.1", type: "CANARY", status: "HEALTHY", traffic: "15%" },
  { version: "v2.5.0", type: "STABLE", status: "HEALTHY", traffic: "85%" },
];

export default function DevOpsCenterPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<SystemHealth>("/monitoring/health");
      setHealth(data);
    } catch (err) {
      console.error("Failed to fetch system health", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleRestart = async (service: string) => {
    try {
      await apiClient.post(`/platform/restart/${service}`, {});
      toast.success(`Service ${service} restarted successfully`);
    } catch (err) {
      toast.error(`Failed to restart service ${service}`);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <RoadmapBanner reason="security score, backups, cost, releases, and incidents are illustrative; only Cluster Health and System Components call a real endpoint" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Platform Operations Center</h1>
          <p className="text-muted-foreground text-sm mt-1">DevSecOps & SRE Dashboard</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-red-500/20 text-red-500 hover:bg-red-500/10">
            <AlertTriangle className="mr-2 w-4 h-4" /> Inject Chaos
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">
            <ArrowUpCircle className="mr-2 w-4 h-4" /> New Release
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cluster Health</CardTitle>
            <Activity className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${health?.status === 'GREEN' ? 'text-green-500' : 'text-amber-500'}`}>
              {loading ? "..." : (health?.status || "99.99%")}
            </div>
            <p className="text-xs text-muted-foreground">{health?.components.length || 5} Nodes Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Security Score</CardTitle>
            <ShieldCheck className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">A+</div>
            <p className="text-xs text-muted-foreground">0 Critical CVEs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Backups</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">14GB</div>
            <p className="text-xs text-muted-foreground">Last sync: 10m ago</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Infrastructure Cost</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$0.00</div>
            <p className="text-xs text-muted-foreground">100% On-Premise (Ollama)</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3 flex-1">
        
        {/* System Components */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle>System Components</CardTitle>
            <CardDescription>Live service health</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {loading ? (
              <div className="text-center text-sm text-muted-foreground">Loading health...</div>
            ) : !health || health.components.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground">No components found.</div>
            ) : (
              <div className="space-y-3">
                {health.components.map((comp) => (
                  <div key={comp} className="flex justify-between items-center p-3 border rounded-lg bg-card shadow-sm">
                    <div>
                      <div className="font-bold capitalize">{comp}</div>
                      <Badge variant="outline" className="mt-1 text-[10px] text-green-500 border-green-500/30">ONLINE</Badge>
                    </div>
                    <Button size="icon" variant="outline" onClick={() => handleRestart(comp)} title={`Restart ${comp}`}>
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Releases & Deployments */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle>Active Deployments</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {releases.map(r => (
              <div key={r.version} className="flex justify-between items-center p-4 border rounded-lg bg-card">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold">{r.version}</h3>
                    <Badge variant="outline">{r.type}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Routing {r.traffic} of traffic</p>
                </div>
                <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20">{r.status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Incident Management */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle>Recent Incidents</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {incidents.map(inc => (
              <div key={inc.id} className="flex justify-between items-center p-4 border rounded-lg bg-card">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold">{inc.title}</h3>
                    {inc.severity === "High" && <Badge variant="destructive">P1</Badge>}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{inc.id} • {inc.time}</p>
                </div>
                <Badge variant={inc.status === "RESOLVED" ? "secondary" : "default"}>{inc.status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
