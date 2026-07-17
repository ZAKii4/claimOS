"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Cpu, Server, HardDrive, Download, Power, Settings2, Activity, Play, Box } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface LocalModel {
  name: string;
  version: string;
  parameters_size: string;
  memory_required_mb: number;
  context_window: number;
  avg_throughput_tps: number;
  supported_languages: string[];
  expertise: string[];
  quality_level: string;
  is_loaded: boolean;
}

interface ClusterStatus {
  status: string;
  nodes: number;
  loaded_models: string[];
}

interface Resources {
  cpu_usage_percent: number;
  ram_usage_gb: number;
  gpu_usage_percent: number;
  vram_usage_gb: number;
  active_models: number;
}

export default function LocalAICenterPage() {
  const [models, setModels] = useState<LocalModel[]>([]);
  const [cluster, setCluster] = useState<ClusterStatus | null>(null);
  const [resources, setResources] = useState<Resources | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [modelsData, clusterData, resourcesData] = await Promise.all([
          apiClient.get<LocalModel[]>("/local-ai/models"),
          apiClient.get<ClusterStatus>("/local-ai/cluster"),
          apiClient.get<Resources>("/local-ai/resources")
        ]);
        
        setModels(modelsData || []);
        setCluster(clusterData);
        setResources(resourcesData);
      } catch (err) {
        console.error("Failed to fetch local AI data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  if (loading && models.length === 0) {
    return <div className="flex items-center justify-center h-64">Loading Local AI Cluster...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Local AI Center</h1>
          <p className="text-muted-foreground mt-1">Manage local open-source LLMs and compute resources.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Settings2 className="w-4 h-4" /> Hardware Settings
          </Button>
          <Button className="gap-2">
            <Download className="w-4 h-4" /> Pull Model
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cluster Status</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-2">
              <span className={`w-3 h-3 rounded-full ${cluster?.status === 'ONLINE' ? 'bg-green-500' : 'bg-red-500 animate-pulse'}`} />
              {cluster?.status || 'UNKNOWN'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">{cluster?.nodes || 0} compute nodes active</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GPU Utilization (VRAM)</CardTitle>
            <Cpu className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resources?.gpu_usage_percent.toFixed(1) || 0}%</div>
            <div className="w-full bg-secondary h-1.5 mt-2 rounded-full overflow-hidden">
              <div 
                className={`h-full ${resources && resources.gpu_usage_percent > 80 ? 'bg-destructive' : 'bg-primary'}`} 
                style={{ width: `${resources?.gpu_usage_percent || 0}%` }} 
              />
            </div>
            <p className="text-xs text-muted-foreground mt-2">{resources?.vram_usage_gb.toFixed(1) || 0} GB Allocated</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Memory</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resources?.ram_usage_gb.toFixed(1) || 0} GB</div>
            <div className="w-full bg-secondary h-1.5 mt-2 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500" style={{ width: `${resources?.cpu_usage_percent || 0}%` }} />
            </div>
            <p className="text-xs text-muted-foreground mt-2">CPU: {resources?.cpu_usage_percent.toFixed(1) || 0}% usage</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resources?.active_models || 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Loaded in VRAM</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Local Model Registry</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {models.map((model) => (
            <Card key={model.name} className={`flex flex-col ${model.is_loaded ? 'border-primary/50 bg-primary/5' : ''}`}>
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg ${model.is_loaded ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                      <Box className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{model.name}</CardTitle>
                      <CardDescription>{model.version}</CardDescription>
                    </div>
                  </div>
                  {model.is_loaded && (
                    <span className="inline-flex items-center rounded-full bg-green-500/10 px-2 py-1 text-xs font-medium text-green-500 ring-1 ring-inset ring-green-500/20">
                      Loaded
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="flex-1 text-sm">
                <div className="grid grid-cols-2 gap-y-3 gap-x-2 text-muted-foreground mb-4">
                  <div>
                    <span className="block text-xs uppercase tracking-wider opacity-70">Params</span>
                    <span className="font-medium text-foreground">{model.parameters_size}</span>
                  </div>
                  <div>
                    <span className="block text-xs uppercase tracking-wider opacity-70">Context</span>
                    <span className="font-medium text-foreground">{(model.context_window / 1000).toFixed(0)}k</span>
                  </div>
                  <div>
                    <span className="block text-xs uppercase tracking-wider opacity-70">Req. Memory</span>
                    <span className="font-medium text-foreground">{(model.memory_required_mb / 1024).toFixed(1)} GB</span>
                  </div>
                  <div>
                    <span className="block text-xs uppercase tracking-wider opacity-70">Throughput</span>
                    <span className="font-medium text-foreground">{model.avg_throughput_tps} tps</span>
                  </div>
                </div>
                <div>
                  <span className="block text-xs uppercase tracking-wider opacity-70 mb-1.5">Expertise</span>
                  <div className="flex flex-wrap gap-1.5">
                    {model.expertise.map(exp => (
                      <span key={exp} className="inline-flex items-center rounded bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-secondary-foreground">
                        {exp}
                      </span>
                    ))}
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-4 border-t flex gap-2">
                {model.is_loaded ? (
                  <Button variant="destructive" className="w-full gap-2">
                    <Power className="w-4 h-4" /> Offload from VRAM
                  </Button>
                ) : (
                  <Button variant="default" className="w-full gap-2">
                    <Play className="w-4 h-4" /> Load to VRAM
                  </Button>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
