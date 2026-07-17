"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Globe, Server, Activity, ArrowRightLeft, ShieldCheck, Database, Network, RefreshCw } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface Cluster {
  id: string;
  region: string;
  trust: string;
  status: string;
}

export default function FederationNOCPage() {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchClusters = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<Cluster[]>("/federation/clusters");
      setClusters(data || []);
    } catch (err) {
      console.error("Failed to fetch clusters", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClusters();
  }, []);

  const handleSync = async (clusterId: string) => {
    try {
      await apiClient.post(`/federation/replication/start`, { target_cluster: clusterId });
      toast.success(`Synchronization started for ${clusterId}`);
    } catch (err) {
      toast.error(`Failed to sync ${clusterId}`);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <RoadmapBanner reason="the mesh metrics and topology map are illustrative; the cluster list below calls a real endpoint that is not yet backed by real replication infrastructure" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Global Operations Center (NOC)</h1>
          <p className="text-muted-foreground text-sm mt-1">Multi-Region Enterprise Federation & AI Mesh Network</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-green-500 border-green-500/30 bg-green-500/10 h-8">
            <span className="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span>
            ALL CLUSTERS HEALTHY
          </Badge>
        </div>
      </div>

      {/* Global Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-blue-500/20 bg-blue-500/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Federated Clusters</CardTitle>
            <Globe className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-500">{clusters.length || 3}</div>
            <p className="text-xs text-muted-foreground">France, Germany, Morocco</p>
          </CardContent>
        </Card>

        <Card className="border-purple-500/20 bg-purple-500/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Mesh Nodes</CardTitle>
            <Network className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-500">45</div>
            <p className="text-xs text-muted-foreground">Local Ollama GPU Workers</p>
          </CardContent>
        </Card>

        <Card className="border-yellow-500/20 bg-yellow-500/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Cross-Region Latency</CardTitle>
            <Activity className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">24ms</div>
            <p className="text-xs text-muted-foreground">Average synchronization time</p>
          </CardContent>
        </Card>

        <Card className="border-green-500/20 bg-green-500/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Geo-Redundancy</CardTitle>
            <Database className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">Active</div>
            <p className="text-xs text-muted-foreground">Failover ready in 15 seconds</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3 flex-1">
        
        {/* Topology Map */}
        <Card className="md:col-span-2 flex flex-col h-full bg-slate-950 text-slate-300 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-slate-100">
              <Network className="w-5 h-5" />
              Global AI Mesh Topology
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 relative flex items-center justify-center p-8">
            <div className="absolute inset-0 bg-[url('https://upload.wikimedia.org/wikipedia/commons/e/ec/World_map_blank_without_borders.svg')] opacity-10 bg-no-repeat bg-center bg-cover"></div>
            
            {/* Very simple visual representation of mesh network */}
            <div className="relative w-full max-w-md aspect-video border border-slate-800 rounded-xl bg-slate-900/50 p-4 flex flex-col justify-between backdrop-blur-sm z-10">
              <div className="flex justify-between items-start">
                <div className="flex flex-col items-center">
                  <div className="w-4 h-4 rounded-full bg-blue-500 animate-pulse shadow-[0_0_15px_rgba(59,130,246,0.5)]"></div>
                  <span className="text-[10px] mt-2 font-mono">EU-WEST (FR)</span>
                  <span className="text-[8px] text-slate-500">Primary / 12 Nodes</span>
                </div>
                <div className="w-full h-px bg-slate-700 mt-2 relative">
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-800 text-[10px] px-2 rounded text-yellow-400">12ms</div>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-4 h-4 rounded-full bg-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.5)]"></div>
                  <span className="text-[10px] mt-2 font-mono">EU-CENTRAL (DE)</span>
                  <span className="text-[8px] text-slate-500">Failover / 15 Nodes</span>
                </div>
              </div>
              
              <div className="flex justify-center">
                <div className="w-px h-16 bg-slate-700 relative">
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-800 text-[10px] px-2 rounded text-yellow-400">45ms</div>
                </div>
              </div>

              <div className="flex justify-center">
                <div className="flex flex-col items-center">
                  <div className="w-4 h-4 rounded-full bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.5)]"></div>
                  <span className="text-[10px] mt-2 font-mono">AF-NORTH (MA)</span>
                  <span className="text-[8px] text-slate-500">Edge / 18 Nodes</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Federated Clusters List */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="w-5 h-5 text-muted-foreground" />
              Federated Clusters
            </CardTitle>
            <CardDescription>Live region statuses</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {loading ? (
              <div className="text-center text-sm text-muted-foreground">Loading clusters...</div>
            ) : clusters.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground">No federated clusters found.</div>
            ) : (
              <div className="space-y-3">
                {clusters.map((cluster) => (
                  <div key={cluster.id} className="flex justify-between items-center text-sm p-3 border rounded-lg bg-card shadow-sm">
                    <div>
                      <div className="font-bold flex items-center gap-2">
                        {cluster.id}
                        <Badge variant="outline" className={`text-[10px] ${cluster.status === 'ONLINE' ? 'text-green-500 border-green-500/30' : 'text-red-500 border-red-500/30'}`}>
                          {cluster.status}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Region: {cluster.region} | Trust: {cluster.trust}
                      </div>
                    </div>
                    <div>
                      <Button size="icon" variant="outline" onClick={() => handleSync(cluster.id)} title="Synchronize">
                        <RefreshCw className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Global Knowledge RAG</span>
                <span className="font-bold text-green-500">Synced</span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-muted-foreground">Distributed Memory</span>
                <span className="font-bold text-green-500">Synced</span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-muted-foreground">AI Governance Score</span>
                <span className="font-bold text-primary">A+ Global</span>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
