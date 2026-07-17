"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  BarChart, 
  Globe, 
  Activity, 
  ShieldCheck, 
  BrainCircuit, 
  FileText, 
  Zap, 
  Users, 
  ArrowRight,
  MonitorCheck,
  Bot
} from "lucide-react";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface PendingClaim {
  id: string;
  external_ref: string;
  date_of_loss: string;
  claim_type_code: string;
  status_code: string;
  composite_confidence: string;
}

export default function CommandCenterPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [pendingClaims, setPendingClaims] = useState<PendingClaim[]>([]);
  const [loadingClaims, setLoadingClaims] = useState(true);

  const fetchPendingClaims = async () => {
    try {
      setLoadingClaims(true);
      const data = await apiClient.get<{items: PendingClaim[]}>("/claims");
      setPendingClaims(data.items.filter(c => c.status_code === "PENDING_REVIEW"));
    } catch (err) {
      console.error("Failed to fetch pending claims", err);
    } finally {
      setLoadingClaims(false);
    }
  };

  useEffect(() => {
    fetchPendingClaims();
  }, []);

  const handleApprove = async (id: string) => {
    try {
      await apiClient.post(`/review/${id}/approve`, {});
      toast.success("Claim approved successfully");
      fetchPendingClaims();
    } catch (err) {
      toast.error("Failed to approve claim");
    }
  };

  const handleEscalate = async (id: string) => {
    try {
      await apiClient.post(`/review/${id}/correct`, { correction_notes: "Escalated for human correction" });
      toast.success("Claim escalated for correction");
      fetchPendingClaims();
    } catch (err) {
      toast.error("Failed to escalate claim");
    }
  };

  return (
    <div className="flex flex-col h-full space-y-4">
      <RoadmapBanner reason="the KPI tower, situation map, and AI recommendations are illustrative; only the Pending Human Review panel is live" />
      {/* Executive Header */}
      <div className="flex justify-between items-center bg-slate-950 text-white p-6 rounded-xl border border-slate-800 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
        <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl translate-y-1/2"></div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <MonitorCheck className="h-8 w-8 text-blue-400" />
            <h1 className="text-4xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              Enterprise Command Center
            </h1>
          </div>
          <p className="text-slate-400 text-lg">AI-Native Strategic Operations & Decision Room</p>
        </div>
        
        <div className="flex gap-4 relative z-10">
          <div className="flex flex-col items-end">
            <span className="text-sm text-slate-400 uppercase tracking-wider font-semibold">System Status</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              <span className="font-bold text-emerald-400">ALL SYSTEMS NOMINAL</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-4 flex-1">
        
        {/* Left Column: KPI Tower */}
        <div className="col-span-3 flex flex-col gap-4">
          <Card className="border-emerald-500/20 shadow-sm bg-emerald-500/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                <Activity className="h-4 w-4" /> Business Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">1.2M €</div>
              <p className="text-xs text-muted-foreground mt-1">Fraud Prevented (YTD)</p>
              <div className="mt-4 pt-4 border-t border-emerald-500/10">
                <div className="text-2xl font-bold">84%</div>
                <p className="text-xs text-muted-foreground">Automation Rate</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="border-blue-500/20 shadow-sm bg-blue-500/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2 text-blue-700 dark:text-blue-400">
                <BrainCircuit className="h-4 w-4" /> AI Operations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">0.01%</div>
              <p className="text-xs text-muted-foreground mt-1">Hallucination Rate</p>
              <div className="mt-4 pt-4 border-t border-blue-500/10">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-semibold">EU AI Act</span>
                  <Badge variant="outline" className="border-emerald-500 text-emerald-500 bg-emerald-500/10 text-[10px]">COMPLIANT</Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-semibold">ISO 42001</span>
                  <Badge variant="outline" className="border-emerald-500 text-emerald-500 bg-emerald-500/10 text-[10px]">CERTIFIED</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="flex-1 border-purple-500/20 shadow-sm bg-purple-500/5">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2 text-purple-700 dark:text-purple-400">
                <FileText className="h-4 w-4" /> Executive Reports
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-between bg-background">
                Board Report Q3 <ArrowRight className="h-3 w-3" />
              </Button>
              <Button variant="outline" className="w-full justify-between bg-background">
                Audit Compliance <ArrowRight className="h-3 w-3" />
              </Button>
              <Button variant="outline" className="w-full justify-between bg-background">
                AI ROI Summary <ArrowRight className="h-3 w-3" />
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Center: Global Situation & Scenarios */}
        <div className="col-span-6 flex flex-col gap-4">
          <Card className="flex-1 bg-slate-950 border-slate-800 text-slate-100 shadow-xl overflow-hidden relative">
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
            <CardHeader className="border-b border-slate-800 pb-3 relative z-10">
              <CardTitle className="text-lg flex justify-between items-center text-slate-100">
                <div className="flex items-center gap-2">
                  <Globe className="h-5 w-5 text-blue-400" />
                  Global Situation Map
                </div>
                <Badge variant="outline" className="bg-slate-900 border-slate-700 text-slate-300">Live Federation: 82 Nodes</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 relative z-10 h-[300px] flex items-center justify-center">
               <div className="text-center space-y-2">
                  <div className="w-24 h-24 rounded-full border-4 border-blue-500 border-dashed animate-[spin_10s_linear_infinite] mx-auto flex items-center justify-center">
                    <Globe className="h-10 w-10 text-blue-500 animate-none" />
                  </div>
                  <p className="text-slate-400 text-sm font-medium">Federated Control Plane Active</p>
                  <p className="text-slate-500 text-xs">EU-Central • EU-West • AF-North</p>
               </div>
            </CardContent>
          </Card>

          <Card className="shadow-md border-red-500/20">
            <CardHeader className="bg-red-500/5 pb-2">
              <CardTitle className="text-sm flex items-center gap-2 text-red-600 dark:text-red-400">
                <Zap className="h-4 w-4" /> Strategic Recommendations (AI Generated)
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg border bg-card">
                <div className="mt-1">
                  <Badge className="bg-red-500 hover:bg-red-600">HIGH URGENCY</Badge>
                </div>
                <div>
                  <h4 className="font-bold text-sm">Increase GPU Capacity in EU-Central</h4>
                  <p className="text-xs text-muted-foreground mt-1">OCR pipeline is facing 400ms queuing delays due to VRAM limits. Projected impact: +24% processing speed. Cost: $500/mo.</p>
                </div>
                <div className="ml-auto">
                  <Button size="sm">Approve</Button>
                </div>
              </div>
              
              <div className="flex items-start gap-3 p-3 rounded-lg border bg-card">
                <div className="mt-1">
                  <Badge variant="outline" className="border-yellow-500 text-yellow-600">MED URGENCY</Badge>
                </div>
                <div>
                  <h4 className="font-bold text-sm">Promote Qwen2.5 for Fraud Investigation</h4>
                  <p className="text-xs text-muted-foreground mt-1">A/B tests show superiority over Phi4 on anomaly detection. Projected impact: +12% accuracy. Cost: None.</p>
                </div>
                <div className="ml-auto">
                  <Button size="sm" variant="outline">Simulate</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Pending Human Review */}
        <div className="col-span-3 flex flex-col h-full">
          <Card className="flex-1 shadow-lg border-primary/20">
            <CardHeader className="bg-primary/5 pb-3">
              <CardTitle className="text-md flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-primary" />
                Pending Human Review
              </CardTitle>
              <CardDescription>Claims requiring your attention</CardDescription>
            </CardHeader>
            <CardContent className="p-4 flex flex-col gap-3">
              {loadingClaims ? (
                <div className="text-center text-sm text-muted-foreground p-4">Loading pending claims...</div>
              ) : pendingClaims.length === 0 ? (
                <div className="text-center text-sm text-muted-foreground p-4">No claims pending review.</div>
              ) : (
                pendingClaims.map((claim) => {
                  const conf = parseFloat(claim.composite_confidence || "0");
                  return (
                    <div key={claim.id} className="p-3 border rounded-lg bg-card shadow-sm relative overflow-hidden">
                      <div className={`absolute top-0 left-0 w-1 h-full ${conf < 0.8 ? 'bg-amber-500' : 'bg-primary'}`}></div>
                      <div className="flex justify-between items-start mb-2 pl-1">
                        <h4 className="font-bold text-sm">{claim.external_ref}</h4>
                        <Badge variant="secondary" className="text-[10px] bg-amber-500/10 text-amber-600">
                          {(conf * 100).toFixed(0)}% AI Conf
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mb-3 pl-1">Type: {claim.claim_type_code}</p>
                      <div className="flex gap-2 w-full pl-1">
                        <Button size="sm" variant="outline" className="flex-1 text-xs" onClick={() => handleEscalate(claim.id)}>
                          Escalate
                        </Button>
                        <Button size="sm" className="flex-1 text-xs" onClick={() => handleApprove(claim.id)}>
                          Approve
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
