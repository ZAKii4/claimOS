"use client";

import React, { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search } from "lucide-react";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  trace_id: string;
}

export default function ObservabilityDashboard() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [traceId, setTraceId] = useState("a1b2c3d4");

  const fetchTraces = async (id: string) => {
    try {
      setLoading(true);
      const data = await apiClient.get<LogEntry[] | any>(`/monitoring/traces/${id}`);
      // Fallback if data is empty object
      const logsData = Array.isArray(data) ? data : [
        { timestamp: new Date().toISOString(), level: "INFO", message: "Fallback: Hybrid RAG search started", trace_id: id },
        { timestamp: new Date(Date.now() + 1000).toISOString(), level: "WARNING", message: "Fallback: Latency anomaly detected", trace_id: id },
      ];
      setLogs(logsData);
      setFilteredLogs(logsData);
    } catch (err) {
      console.error("Failed to fetch traces", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTraces(traceId);
  }, [traceId]);

  const handleFilter = (level: string) => {
    setFilterLevel(level);
    if (level === "ALL") {
      setFilteredLogs(logs);
    } else {
      setFilteredLogs(logs.filter(log => log.level === level));
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <RoadmapBanner reason="global health/SLO/anomaly counts and capacity forecasting are illustrative; the trace search below is wired to a real endpoint (with a labeled fallback)" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">claimOS Telemetry & AIOps</h1>
          <p className="text-muted-foreground text-sm mt-1">Enterprise Observability Command Center</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Global System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">HEALTHY</p>
            <p className="text-xs text-green-600 mt-1">PostgreSQL, Neo4j, Ollama OK</p>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Service Availability (SLO)</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">99.95%</p>
            <p className="text-xs text-blue-600 mt-1">Target: 99.90%</p>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-yellow-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">AIOps Anomalies</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">2</p>
            <p className="text-xs text-yellow-600 mt-1">VRAM Warning, Latency Spike</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1">
        <Card className="lg:col-span-2 flex flex-col h-full bg-slate-950 border-slate-800 text-slate-300">
          <CardHeader className="border-b border-slate-800 pb-3">
            <div className="flex justify-between items-center">
              <CardTitle className="text-slate-100 flex items-center gap-2">
                Live Traces & JSON Logs
              </CardTitle>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
                  <Input 
                    type="text" 
                    placeholder="Trace ID..." 
                    value={traceId}
                    onChange={(e) => setTraceId(e.target.value)}
                    className="pl-8 h-9 text-xs w-48 bg-slate-900 border-slate-700 text-slate-200" 
                  />
                </div>
                <div className="flex bg-slate-900 rounded-md p-1 border border-slate-800">
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className={`h-7 text-xs px-2 ${filterLevel === 'ALL' ? 'bg-slate-800 text-white' : 'text-slate-400'}`}
                    onClick={() => handleFilter('ALL')}
                  >All</Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className={`h-7 text-xs px-2 ${filterLevel === 'INFO' ? 'bg-blue-900/50 text-blue-400' : 'text-slate-400'}`}
                    onClick={() => handleFilter('INFO')}
                  >INFO</Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className={`h-7 text-xs px-2 ${filterLevel === 'WARNING' ? 'bg-yellow-900/50 text-yellow-400' : 'text-slate-400'}`}
                    onClick={() => handleFilter('WARNING')}
                  >WARN</Button>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 p-4 font-mono text-xs overflow-auto">
            {loading ? (
              <div className="text-slate-500">Loading traces for {traceId}...</div>
            ) : filteredLogs.length === 0 ? (
              <div className="text-slate-500">No logs found.</div>
            ) : (
              <div className="space-y-2">
                {filteredLogs.map((log, i) => (
                  <div key={i} className="bg-slate-900 p-3 rounded border border-slate-800 flex gap-4">
                    <span className="text-slate-500 shrink-0">{new Date(log.timestamp).toLocaleTimeString()}</span>
                    <span className={`shrink-0 w-16 ${log.level === 'INFO' ? 'text-blue-400' : log.level === 'WARNING' ? 'text-yellow-400' : 'text-red-400'}`}>[{log.level}]</span>
                    <span className="text-green-400 break-words">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle>Capacity Forecasting (AIOps)</CardTitle>
          </CardHeader>
          <CardContent className="flex-1">
            <ul className="space-y-4">
              <li className="flex justify-between items-center border-b pb-4">
                <span className="text-sm font-medium">Database Saturation</span>
                <span className="text-sm text-muted-foreground">124 Days Remaining</span>
              </li>
              <li className="flex justify-between items-center border-b pb-4">
                <span className="text-sm font-medium">GPU VRAM Trend</span>
                <span className="text-sm text-red-500 font-bold">Increasing (+15%/mo)</span>
              </li>
              <li className="flex justify-between items-center pt-2">
                <span className="text-sm font-medium">Recommendation</span>
                <Badge variant="outline" className="text-blue-500 border-blue-500/30">Provision new node</Badge>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
