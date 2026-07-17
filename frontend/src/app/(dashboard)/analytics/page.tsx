"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Activity, ShieldAlert, CheckCircle2, TrendingUp, AlertTriangle, Cpu, BrainCircuit, FileSearch } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import { apiClient } from "@/lib/api-client";

interface AnalyticsKPIs {
  total_claims: number;
  automation_rate: number;
  override_rate: number;
  ocr_cer: number;
  classification_f1: number;
}

interface AnalyticsTrends {
  claims_processed: number;
  fraud_prevented: number;
  active_agents: number;
  automation_rate: number;
  chart_data: Array<{name: string, claims: number, fraud: number}>;
}

interface AnalyticsQuality {
  total_records_checked: number;
  issues_found: number;
  quality_score: number;
}

export default function AnalyticsPage() {
  const [kpis, setKpis] = useState<AnalyticsKPIs | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrends | null>(null);
  const [quality, setQuality] = useState<AnalyticsQuality | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [kpiData, trendData, qualityData] = await Promise.all([
          apiClient.get<AnalyticsKPIs>("/analytics/kpis", { tenant_id: "default" }),
          apiClient.get<AnalyticsTrends>("/analytics/dashboards", { tenant_id: "default" }),
          apiClient.get<AnalyticsQuality>("/analytics/quality", { tenant_id: "default" })
        ]);
        
        setKpis(kpiData);
        setTrends(trendData);
        setQuality(qualityData);
      } catch (err) {
        console.error("Failed to fetch analytics data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 60000); // refresh every 60s
    return () => clearInterval(interval);
  }, []);

  if (loading && !kpis) {
    return <div className="flex items-center justify-center h-64">Loading Analytics Engine...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Center</h1>
          <p className="text-muted-foreground mt-1">Deep insights into AI performance and operational metrics.</p>
        </div>
        <div className="flex gap-2">
          <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary ring-1 ring-inset ring-primary/20">
            Real-time Aggregation
          </span>
        </div>
      </div>

      {kpis && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Claims</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpis.total_claims.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">Processed across pipeline</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Automation Rate</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpis.automation_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">Straight-through processing</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Human Overrides</CardTitle>
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpis.override_rate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">Required intervention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">OCR Error Rate</CardTitle>
              <FileSearch className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(kpis.ocr_cer * 100).toFixed(2)}%</div>
              <p className="text-xs text-muted-foreground">Character error rate (CER)</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Classification (F1)</CardTitle>
              <BrainCircuit className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpis.classification_f1.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">Model confidence score</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {trends && (
          <Card className="col-span-2">
            <CardHeader>
              <CardTitle>Processing Volume Trends</CardTitle>
              <CardDescription>Hourly breakdown of claim ingestion vs fraud detection</CardDescription>
            </CardHeader>
            <CardContent className="pl-2">
              <div className="h-[350px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trends.chart_data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorClaims" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" vertical={false} />
                    <XAxis dataKey="name" className="text-xs" stroke="hsl(var(--muted-foreground))" />
                    <YAxis className="text-xs" stroke="hsl(var(--muted-foreground))" />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                      itemStyle={{ color: 'hsl(var(--foreground))' }}
                    />
                    <Legend />
                    <Area type="monotone" dataKey="claims" name="Total Claims" stroke="hsl(var(--primary))" fillOpacity={1} fill="url(#colorClaims)" />
                    <Area type="monotone" dataKey="fraud" name="Fraud Detected" stroke="hsl(var(--destructive))" fillOpacity={1} fill="url(#colorFraud)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {quality && (
          <Card className="col-span-1 flex flex-col">
            <CardHeader>
              <CardTitle>Data Quality Audit</CardTitle>
              <CardDescription>Continuous database validation</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-center">
              <div className="space-y-8">
                <div className="flex flex-col items-center justify-center text-center">
                  <div className="relative flex items-center justify-center">
                    <svg className="w-32 h-32 transform -rotate-90">
                      <circle
                        className="text-muted/20"
                        strokeWidth="12"
                        stroke="currentColor"
                        fill="transparent"
                        r="58"
                        cx="64"
                        cy="64"
                      />
                      <circle
                        className="text-green-500"
                        strokeWidth="12"
                        strokeDasharray={364}
                        strokeDashoffset={364 - (364 * quality.quality_score) / 100}
                        strokeLinecap="round"
                        stroke="currentColor"
                        fill="transparent"
                        r="58"
                        cx="64"
                        cy="64"
                      />
                    </svg>
                    <div className="absolute flex flex-col items-center justify-center">
                      <span className="text-3xl font-bold">{quality.quality_score}%</span>
                      <span className="text-xs text-muted-foreground uppercase tracking-wider">Score</span>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                  <div className="text-center">
                    <div className="text-2xl font-semibold">{quality.total_records_checked.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">Records Scanned</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-semibold text-destructive">{quality.issues_found.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">Anomalies Found</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
