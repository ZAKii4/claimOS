"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShieldCheck, Scale, CheckCircle2, TrendingUp, Cpu, Server, Network, Database } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface AIModel {
  id: string;
  name: string;
  version: string;
  status: string;
  score: string;
  eu_act: string;
}

interface Dataset {
  id: string;
  name: string;
  description: string;
  size_mb: number;
  pii_compliant: boolean;
}

export default function AIGovernanceCenter() {
  const [models, setModels] = useState<AIModel[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [modelsData, datasetsData] = await Promise.all([
        apiClient.get<AIModel[]>("/ai-governance/models").catch(() => []),
        apiClient.get<Dataset[]>("/ai-governance/datasets").catch(() => [])
      ]);
      setModels(modelsData || []);
      setDatasets(datasetsData || []);
    } catch (err) {
      console.error("Error fetching governance data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAudit = async (datasetId: string) => {
    try {
      await apiClient.post(`/governance/audit/${datasetId}`, {});
      toast.success("Audit initiated for dataset");
    } catch (err) {
      toast.error("Failed to initiate audit");
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <RoadmapBanner reason="the scorecard, EU AI Act status, and explainability figures are illustrative — only the model/dataset lists below (with their own labeled fallbacks) call real endpoints" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Governance Center</h1>
          <p className="text-muted-foreground text-sm mt-1">EU AI Act & ISO 42001 Compliance Portal</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-green-500/20 text-green-500 hover:bg-green-500/10">
            <CheckCircle2 className="mr-2 w-4 h-4" /> Run Compliance Audit
          </Button>
          <Button className="bg-primary">
            <ShieldCheck className="mr-2 w-4 h-4" /> Register Model
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Models in Production</CardTitle>
            <Server className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">{models.length}</div>
            <p className="text-xs text-muted-foreground">Local Ollama instances</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Global AI Scorecard</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">A+</div>
            <p className="text-xs text-muted-foreground">Accuracy: 98% | Bias: 1%</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">EU AI Act Status</CardTitle>
            <Scale className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">COMPLIANT</div>
            <p className="text-xs text-muted-foreground">All risks mitigated</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Explainability</CardTitle>
            <Network className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">100%</div>
            <p className="text-xs text-muted-foreground">Decisions Graph-Traced</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 flex-1">
        
        {/* Model Registry List */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-muted-foreground" />
              Enterprise Model Registry
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto space-y-4">
            <div className="border rounded-md">
              <div className="grid grid-cols-6 gap-4 p-4 font-semibold text-sm border-b bg-muted/50">
                <div className="col-span-2">Model Name</div>
                <div>Version</div>
                <div>Status</div>
                <div>EU Risk</div>
                <div>Score</div>
              </div>
              <div className="divide-y">
                {loading ? (
                  <div className="p-8 text-center text-muted-foreground">Loading models...</div>
                ) : models.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">
                    <p>No models registered.</p>
                    <p className="text-xs mt-1">Using fallback UI data</p>
                    <div className="grid grid-cols-6 gap-4 p-4 items-center text-sm text-left mt-4 border-t">
                      <div className="col-span-2 font-medium">phi4-claims-extraction</div>
                      <div>1.0</div>
                      <div><Badge>PRODUCTION</Badge></div>
                      <div><Badge variant="outline" className="text-primary">LIMITED_RISK</Badge></div>
                      <div><span className="font-bold text-green-500">A+</span></div>
                    </div>
                  </div>
                ) : models.map(m => (
                  <div key={m.id} className="grid grid-cols-6 gap-4 p-4 items-center text-sm">
                    <div className="col-span-2 font-medium">{m.name}</div>
                    <div>{m.version}</div>
                    <div>
                      <Badge variant={m.status === 'PRODUCTION' ? 'default' : 'secondary'}>{m.status}</Badge>
                    </div>
                    <div>
                      <Badge variant={m.eu_act === 'HIGH_RISK' ? 'destructive' : 'outline'} className={m.eu_act === 'HIGH_RISK' ? '' : 'text-primary'}>
                        {m.eu_act}
                      </Badge>
                    </div>
                    <div>
                      <span className="font-bold text-green-500">{m.score}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Datasets List */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-muted-foreground" />
              Governance Datasets
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto space-y-4">
            <div className="border rounded-md">
              <div className="grid grid-cols-5 gap-4 p-4 font-semibold text-sm border-b bg-muted/50">
                <div className="col-span-2">Dataset Name</div>
                <div>Size (MB)</div>
                <div>PII Compliant</div>
                <div>Actions</div>
              </div>
              <div className="divide-y">
                {loading ? (
                  <div className="p-8 text-center text-muted-foreground">Loading datasets...</div>
                ) : datasets.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">
                    <p>No datasets found.</p>
                    <p className="text-xs mt-1">Using fallback UI data</p>
                    <div className="grid grid-cols-5 gap-4 p-4 items-center text-sm text-left mt-4 border-t">
                      <div className="col-span-2 font-medium">Claims_Q1_2026</div>
                      <div>1,402</div>
                      <div><Badge variant="outline" className="text-green-500 border-green-500/30">YES</Badge></div>
                      <div>
                        <Button size="sm" variant="outline" onClick={() => handleAudit("ds-01")}>Audit</Button>
                      </div>
                    </div>
                  </div>
                ) : datasets.map(d => (
                  <div key={d.id} className="grid grid-cols-5 gap-4 p-4 items-center text-sm">
                    <div className="col-span-2 font-medium">{d.name}</div>
                    <div>{d.size_mb}</div>
                    <div>
                      <Badge variant="outline" className={d.pii_compliant ? 'text-green-500 border-green-500/30' : 'text-red-500 border-red-500/30'}>
                        {d.pii_compliant ? 'YES' : 'NO'}
                      </Badge>
                    </div>
                    <div>
                      <Button size="sm" variant="outline" onClick={() => handleAudit(d.id)}>Audit</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
