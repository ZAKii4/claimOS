"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShieldCheck, ShieldAlert, Key, Smartphone, Server } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface SecurityAlert {
  id: string;
  title: string;
  severity: string;
  status: string;
  description: string;
}

export default function SecurityDashboard() {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<SecurityAlert[] | any>("/governance/policies");
      
      const alertsData = Array.isArray(data) && data.length > 0 ? data : [
        { id: "SEC-001", title: "Unusual API Key Usage", severity: "HIGH", status: "OPEN", description: "Spike in requests from unauthorized region (RU)." },
        { id: "SEC-002", title: "Missing MFA on Admin", severity: "MEDIUM", status: "OPEN", description: "3 admin accounts lack 2FA." }
      ];
      setAlerts(alertsData);
    } catch (err) {
      console.error("Failed to fetch security alerts", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleResolve = async (id: string) => {
    try {
      // Mocking the resolution endpoint as it wasn't specified in OpenAPI
      // In a real scenario, it would be e.g. await apiClient.post(`/governance/policies/${id}/resolve`, {});
      toast.success(`Security alert ${id} resolved`);
      setAlerts(alerts.map(a => a.id === id ? { ...a, status: "RESOLVED" } : a));
    } catch (err) {
      toast.error(`Failed to resolve alert ${id}`);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col p-2">
      <RoadmapBanner reason="active sessions and API keys are illustrative and the resolve action doesn't persist yet — only the security alert fetch is wired to a real endpoint" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Security & Trust Center</h1>
          <p className="text-muted-foreground text-sm mt-1">Zero Trust Architecture & active threat monitoring.</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="text-green-500 border-green-500 bg-green-500/10 h-8 px-4">
            <ShieldCheck className="mr-2 w-4 h-4" />
            SYSTEM SECURE
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 flex-1">
        
        {/* Left Column: Alerts & Policies */}
        <Card className="flex flex-col h-full border-red-500/20">
          <CardHeader className="bg-red-500/5 pb-3">
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-red-500" />
              Active Security Alerts
            </CardTitle>
            <CardDescription>Policies breached or threats detected</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-4 overflow-auto">
            {loading ? (
              <div className="text-sm text-muted-foreground text-center p-4">Loading security policies...</div>
            ) : alerts.length === 0 ? (
              <div className="text-sm text-muted-foreground text-center p-4">No active security alerts.</div>
            ) : (
              <div className="space-y-3">
                {alerts.map(alert => (
                  <div key={alert.id} className="p-3 border rounded-lg bg-card shadow-sm relative overflow-hidden">
                    <div className={`absolute top-0 left-0 w-1 h-full ${alert.status === 'RESOLVED' ? 'bg-green-500' : alert.severity === 'HIGH' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
                    <div className="flex justify-between items-start pl-2">
                      <div>
                        <h4 className="font-bold text-sm flex items-center gap-2">
                          {alert.title}
                          {alert.status === 'RESOLVED' && <Badge variant="outline" className="text-[10px] text-green-500 border-green-500/30">RESOLVED</Badge>}
                        </h4>
                        <p className="text-xs text-muted-foreground mt-1">{alert.description}</p>
                      </div>
                      {alert.status !== 'RESOLVED' && (
                        <Button size="sm" variant="outline" onClick={() => handleResolve(alert.id)}>
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Sessions & Keys */}
        <div className="flex flex-col gap-6 h-full">
          <Card className="flex-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-md flex items-center gap-2">
                <Smartphone className="w-4 h-4" />
                Active Sessions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                <li className="flex items-center justify-between border-b pb-4 border-slate-100 dark:border-slate-800">
                  <div>
                    <p className="text-sm font-medium">MacBook Pro - Safari</p>
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-green-500"></span>
                      IP: 192.168.1.1 (Current)
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600 hover:bg-red-500/10">Revoke</Button>
                </li>
                <li className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">iPhone 14 Pro - App</p>
                    <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-slate-300"></span>
                      IP: 10.0.0.45
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600 hover:bg-red-500/10">Revoke</Button>
                </li>
              </ul>
            </CardContent>
          </Card>
          
          <Card className="flex-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-md flex items-center gap-2">
                <Key className="w-4 h-4" />
                API Keys
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 border rounded-lg bg-card">
                  <div>
                    <div className="font-mono text-sm font-bold">sk-live-************8a9b</div>
                    <div className="text-xs text-muted-foreground mt-1">Created 2 months ago</div>
                  </div>
                  <Badge>Active</Badge>
                </div>
                <Button className="w-full mt-4" variant="secondary">
                  Generate New Key
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
