"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Search, Bot, GitGraph, FileText, CheckCircle2, AlertTriangle, MessageSquare, Network, Lightbulb, ArrowRightLeft } from "lucide-react";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface GraphNode {
  id: string;
  label: string;
  group: string;
}

interface GraphEdge {
  from: string;
  to: string;
  label: string;
}

interface GraphData {
  claim_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function InvestigationWorkspacePage() {
  const [chatInput, setChatInput] = useState("");
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const claimId = "CLM-2026-000154";

  useEffect(() => {
    apiClient.get<GraphData>(`/investigation/graph/${claimId}`)
      .then(data => setGraphData(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div className="flex flex-col h-full space-y-4">
      <RoadmapBanner reason="the timeline, case comparison, decision intelligence, recommendations, and copilot chat are scripted illustrations; only the evidence graph is fetched from an API" />
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Investigation Workspace</h1>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className="text-blue-500 border-blue-500 bg-blue-500/10">CLM-2026-000154</Badge>
            <span className="text-muted-foreground text-sm">Enterprise Decision Intelligence Copilot</span>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input type="search" placeholder="Global Enterprise Search..." className="pl-8 w-64" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4 flex-1 min-h-0">
        
        {/* Left Column: Timeline & Comparison */}
        <div className="col-span-3 flex flex-col gap-4 overflow-auto pb-4">
          <Card className="flex-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-md flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Case Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 dark:before:via-slate-700 before:to-transparent">
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-6 h-6 rounded-full border border-white bg-slate-300 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 dark:bg-slate-700 dark:border-slate-800 dark:text-slate-100">
                  <CheckCircle2 className="w-3 h-3 text-green-500" />
                </div>
                <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.5rem)] p-3 rounded border bg-card shadow-sm">
                  <div className="font-bold">Claim Created</div>
                  <div className="text-xs text-muted-foreground mt-1">2 mins ago</div>
                </div>
              </div>
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-6 h-6 rounded-full border border-white bg-slate-300 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 dark:bg-slate-700 dark:border-slate-800 dark:text-slate-100">
                  <Bot className="w-3 h-3 text-blue-500" />
                </div>
                <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.5rem)] p-3 rounded border bg-card shadow-sm">
                  <div className="font-bold">OCR Processed</div>
                  <div className="text-xs text-muted-foreground mt-1">Confidence 98%</div>
                </div>
              </div>
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-6 h-6 rounded-full border border-white bg-slate-300 text-slate-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 dark:bg-slate-700 dark:border-slate-800 dark:text-slate-100">
                  <AlertTriangle className="w-3 h-3 text-yellow-500" />
                </div>
                <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.5rem)] p-3 rounded border bg-yellow-500/10 border-yellow-500/30 shadow-sm">
                  <div className="font-bold text-yellow-600 dark:text-yellow-400">Agent Review</div>
                  <div className="text-xs text-muted-foreground mt-1">Manual review needed</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-md flex items-center gap-2">
                <ArrowRightLeft className="h-4 w-4" />
                Case Comparison
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="p-3 border rounded bg-card text-sm">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold">vs CLM-2025-0099</span>
                  <Badge variant="outline" className="text-red-500 border-red-500/30">92% Similar</Badge>
                </div>
                <p className="text-xs text-muted-foreground">Same fraudulent network suspected based on Document Similarity & OCR pattern.</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Center Column: Evidence Graph & RAG */}
        <div className="col-span-6 flex flex-col gap-4">
          <Card className="flex-1 flex flex-col bg-slate-950 text-slate-200 border-slate-800">
            <CardHeader className="pb-2 border-b border-slate-800">
              <CardTitle className="text-md flex justify-between items-center text-slate-100">
                <div className="flex items-center gap-2">
                  <Network className="h-4 w-4" />
                  Interactive Evidence Graph
                </div>
                <div className="flex gap-2">
                  <Badge variant="outline" className="text-slate-400 border-slate-700 text-[10px]">Filter: Entities</Badge>
                  <Badge variant="outline" className="text-slate-400 border-slate-700 text-[10px]">Zoom: 100%</Badge>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 relative flex flex-col items-center justify-center min-h-[300px] overflow-hidden p-4">
              {graphData ? (
                <div className="w-full flex flex-wrap gap-4 justify-center items-center">
                  {graphData.nodes.map(node => (
                    <div key={node.id} className="flex flex-col items-center p-3 border rounded-lg bg-card shadow-sm w-32">
                      <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center ${node.group === 'Document' ? 'border-blue-500 bg-blue-900/30 text-blue-400' : node.group === 'PolicyHolder' ? 'border-purple-500 bg-purple-900/30 text-purple-400' : 'border-red-500 bg-red-900/30 text-red-400'}`}>
                        {node.group === 'Document' ? <FileText className="w-5 h-5" /> : node.group === 'PolicyHolder' ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                      </div>
                      <span className="text-xs mt-2 text-center font-bold break-words w-full">{node.label}</span>
                      <span className="text-[10px] text-muted-foreground mt-1 text-center">{node.group}</span>
                    </div>
                  ))}
                  
                  {graphData.edges.length > 0 && (
                     <div className="w-full mt-4 p-4 border-t border-slate-800 text-xs text-muted-foreground text-center">
                        <span className="font-bold">Relations:</span> {graphData.edges.map(e => `${e.from} → [${e.label}] → ${e.to}`).join(' | ')}
                     </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">Loading evidence graph...</div>
              )}
            </CardContent>
          </Card>
          
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Decision Intelligence
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span>Confidence</span> <span className="font-bold text-green-500">HIGH</span></div>
                  <div className="flex justify-between"><span>Risk Level</span> <span className="font-bold text-green-500">LOW</span></div>
                  <div className="flex justify-between"><span>Explainability</span> <span className="font-bold text-blue-500">A+</span></div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-yellow-500" />
                  Smart Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-xs">
                  <Badge variant="outline" className="text-green-500 border-green-500">HIGH ROI</Badge>
                  Request Police Report
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <Badge variant="outline" className="text-yellow-500 border-yellow-500">MED ROI</Badge>
                  Consult Legal Advisor
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Right Column: AI Copilot */}
        <div className="col-span-3 flex flex-col h-full">
          <Card className="flex-1 flex flex-col border-primary/20 shadow-lg">
            <CardHeader className="bg-primary/5 pb-3">
              <CardTitle className="text-md flex items-center gap-2">
                <Bot className="h-5 w-5 text-primary" />
                Decision Copilot
              </CardTitle>
              <CardDescription>Ask questions about this claim</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto p-4 space-y-4">
              <div className="flex justify-end">
                <div className="bg-primary text-primary-foreground p-3 rounded-xl max-w-[85%] text-sm rounded-tr-none">
                  Pourquoi ce dossier est-il passé en revue humaine ?
                </div>
              </div>
              <div className="flex justify-start">
                <div className="bg-muted p-3 rounded-xl max-w-[85%] text-sm rounded-tl-none space-y-2">
                  <p>Based on the analysis, this claim triggers 3 alerts.</p>
                  <ul className="list-disc pl-4 text-xs text-muted-foreground">
                    <li>OCR confidence was 98% (Normal)</li>
                    <li>Fraud score elevated (Rule 44)</li>
                  </ul>
                  <p className="font-bold text-xs">Recommendation: Request manual invoice review.</p>
                  <div className="pt-2 flex gap-1">
                    <Badge variant="secondary" className="text-[9px]">Invoice_OCR_Result.json</Badge>
                    <Badge variant="secondary" className="text-[9px]">FraudRule_44</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
            <div className="p-3 border-t bg-card mt-auto">
              <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); setChatInput(""); }}>
                <Input 
                  placeholder="Ask the Copilot..." 
                  className="flex-1 bg-background" 
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                />
                <Button type="submit" size="icon">
                  <MessageSquare className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
