"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Settings, Save, Server, Shield, Bell, Network, Database } from "lucide-react";
import { toast } from "sonner";
import { RoadmapBanner } from "@/components/RoadmapBanner";

export default function SettingsPage() {
  const [loading, setLoading] = useState(false);

  const handleSave = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      toast.success("System settings updated successfully.");
    }, 800);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <RoadmapBanner reason="this entire page is a static mockup — no settings are actually read from or saved to the server yet" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
          <p className="text-muted-foreground mt-1 text-sm">Configure global claimOS parameters and core integrations.</p>
        </div>
        <Button onClick={handleSave} disabled={loading} className="gap-2">
          <Save className="w-4 h-4" />
          {loading ? "Saving..." : "Save Changes"}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Navigation/Sidebar equivalent for Settings */}
        <div className="space-y-2">
          <Card className="bg-primary/5 border-primary/20 cursor-pointer">
            <CardContent className="p-4 flex items-center gap-3">
              <Server className="w-5 h-5 text-primary" />
              <div className="font-medium text-sm">General Platform</div>
            </CardContent>
          </Card>
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="p-4 flex items-center gap-3">
              <Database className="w-5 h-5 text-muted-foreground" />
              <div className="font-medium text-sm">Data & Retention</div>
            </CardContent>
          </Card>
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="p-4 flex items-center gap-3">
              <Network className="w-5 h-5 text-muted-foreground" />
              <div className="font-medium text-sm">Network Federation</div>
            </CardContent>
          </Card>
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="p-4 flex items-center gap-3">
              <Shield className="w-5 h-5 text-muted-foreground" />
              <div className="font-medium text-sm">Security & IAM</div>
            </CardContent>
          </Card>
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="p-4 flex items-center gap-3">
              <Bell className="w-5 h-5 text-muted-foreground" />
              <div className="font-medium text-sm">Alerts & Notifications</div>
            </CardContent>
          </Card>
        </div>

        {/* Settings Content */}
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Environment Configuration</CardTitle>
              <CardDescription>Global variables for the current cluster</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <label className="text-sm font-medium">Cluster ID</label>
                <div className="flex gap-2">
                  <Input defaultValue="cluster-eu-west-primary" disabled />
                  <Badge variant="outline" className="shrink-0 bg-muted text-muted-foreground">Read-only</Badge>
                </div>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Global API URL</label>
                <Input defaultValue="https://api.claimos.internal/v1" />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium">Default Locale</label>
                <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
                  <option>en-US</option>
                  <option>fr-FR</option>
                  <option>de-DE</option>
                </select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Local AI Worker Limits</CardTitle>
              <CardDescription>Configure Ollama resource boundaries</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <label className="text-sm font-medium flex justify-between">
                  <span>Max Concurrent Models</span>
                  <span className="text-muted-foreground text-xs">Recommended: 3</span>
                </label>
                <Input type="number" defaultValue="3" />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium flex justify-between">
                  <span>VRAM Reservation (%)</span>
                  <span className="text-muted-foreground text-xs">For system GUI fallback</span>
                </label>
                <Input type="number" defaultValue="10" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="text-lg text-destructive">Danger Zone</CardTitle>
              <CardDescription>Actions here cannot be easily undone.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-sm">Purge Analytics Cache</h4>
                  <p className="text-xs text-muted-foreground mt-1">Clears Redis cache for dashboard metrics.</p>
                </div>
                <Button variant="outline" className="text-destructive border-destructive hover:bg-destructive/10">Purge Cache</Button>
              </div>
              <div className="flex items-center justify-between border-t pt-4">
                <div>
                  <h4 className="font-bold text-sm">Force Cluster Resync</h4>
                  <p className="text-xs text-muted-foreground mt-1">Re-syncs Neo4j knowledge graph from federation primary.</p>
                </div>
                <Button variant="outline" className="text-destructive border-destructive hover:bg-destructive/10">Resync Now</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
