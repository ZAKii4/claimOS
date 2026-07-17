"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BookOpen, Terminal, Blocks, DownloadCloud, Code2, Link, Zap } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { RoadmapBanner } from "@/components/RoadmapBanner";

interface SDKPackage {
  id: string;
  name: string;
  author: string;
  downloads: number;
  version: string;
}

export default function DeveloperCenterPage() {
  const [plugins, setPlugins] = useState<SDKPackage[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPlugins = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<SDKPackage[]>("/platform-sdk/plugins");
      setPlugins(data || []);
    } catch (err) {
      console.error("Failed to fetch plugins", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  const handleDeploy = async (pluginId: string) => {
    try {
      await apiClient.post("/platform-sdk/plugins/install", { plugin_id: pluginId });
      toast.success(`Plugin ${pluginId} installed successfully`);
      fetchPlugins();
    } catch (err) {
      toast.error(`Failed to install plugin ${pluginId}`);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <RoadmapBanner reason="the hero cards and CLI terminal are static mockups; the plugin list below calls a real endpoint and clearly labels its own fallback data" />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Platform Developer Center</h1>
          <p className="text-muted-foreground text-sm mt-1">SDK, CLI, Plugins, & Webhooks API Explorer</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-primary/20 text-primary hover:bg-primary/10">
            <Terminal className="mr-2 w-4 h-4" /> Download CLI
          </Button>
          <Button className="bg-primary">
            <Blocks className="mr-2 w-4 h-4" /> Build Plugin
          </Button>
        </div>
      </div>

      {/* Hero Links */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="flex flex-col items-start space-y-2 pb-2">
            <Code2 className="h-6 w-6 text-blue-500 group-hover:scale-110 transition-transform" />
            <CardTitle className="text-md">SDK Documentation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Access Python and TypeScript SDK references for building.</p>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="flex flex-col items-start space-y-2 pb-2">
            <Link className="h-6 w-6 text-purple-500 group-hover:scale-110 transition-transform" />
            <CardTitle className="text-md">API Explorer</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Interactive REST, WebSocket, and MCP endpoint tester.</p>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="flex flex-col items-start space-y-2 pb-2">
            <Zap className="h-6 w-6 text-yellow-500 group-hover:scale-110 transition-transform" />
            <CardTitle className="text-md">Event Hooks</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Subscribe to global events like FraudDetected or OCRFinished.</p>
          </CardContent>
        </Card>

        <Card className="hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader className="flex flex-col items-start space-y-2 pb-2">
            <DownloadCloud className="h-6 w-6 text-green-500 group-hover:scale-110 transition-transform" />
            <CardTitle className="text-md">Marketplace</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">Browse pre-built agents, workflows, and OCR pipelines.</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 flex-1">
        
        {/* Marketplace Highlight */}
        <Card className="flex flex-col h-full">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Blocks className="w-5 h-5 text-muted-foreground" />
              Featured Plugins
            </CardTitle>
            <CardDescription>Install official and community-built modules</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-4">
            {loading ? (
              <div className="text-center text-sm text-muted-foreground">Loading plugins...</div>
            ) : plugins.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground">
                <p>No plugins available at the moment.</p>
                <div className="mt-4 pt-4 border-t text-left">
                  <p className="mb-2">Fallback mock plugins:</p>
                  <div className="flex justify-between items-center p-4 border rounded-lg bg-card mb-2">
                    <div>
                      <h3 className="font-bold">Advanced OCR Connector</h3>
                      <p className="text-xs text-muted-foreground mt-1">By claimOS • 120 Downloads • v1.0.0</p>
                    </div>
                    <Button size="sm" variant="secondary" onClick={() => handleDeploy("plug-ocr")}>Install</Button>
                  </div>
                  <div className="flex justify-between items-center p-4 border rounded-lg bg-card">
                    <div>
                      <h3 className="font-bold">EU Compliance Pack</h3>
                      <p className="text-xs text-muted-foreground mt-1">By EU Security • 540 Downloads • v2.1.0</p>
                    </div>
                    <Button size="sm" variant="secondary" onClick={() => handleDeploy("plug-eu")}>Install</Button>
                  </div>
                </div>
              </div>
            ) : (
              plugins.map(p => (
                <div key={p.id} className="flex justify-between items-center p-4 border rounded-lg bg-card">
                  <div>
                    <h3 className="font-bold">{p.name}</h3>
                    <p className="text-xs text-muted-foreground mt-1">By {p.author} • {p.downloads} Downloads • {p.version}</p>
                  </div>
                  <Button size="sm" variant="secondary" onClick={() => handleDeploy(p.id)}>Install</Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* CLI Terminal Mockup */}
        <Card className="flex flex-col h-full bg-black border-slate-800 text-slate-300 font-mono text-sm shadow-xl">
          <CardHeader className="border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="ml-2 text-xs text-slate-500 font-sans">claimctl — claimOS Enterprise</span>
            </div>
          </CardHeader>
          <CardContent className="flex-1 p-4 space-y-2 overflow-auto">
            <div className="flex gap-2">
              <span className="text-green-400">➜</span>
              <span className="text-blue-400">~</span>
              <span className="text-white">claimctl login</span>
            </div>
            <div className="text-slate-400">Logging into local claimOS cluster... Success.</div>
            <div className="flex gap-2 mt-4">
              <span className="text-green-400">➜</span>
              <span className="text-blue-400">~</span>
              <span className="text-white">claimctl plugins list</span>
            </div>
            <div className="text-slate-400">
              ID            NAME                     STATUS <br/>
              plug-101      FraudDetection           <span className="text-green-400">ENABLED</span> <br/>
              plug-102      ExternalOCR              <span className="text-yellow-400">DISABLED</span> <br/>
            </div>
            <div className="flex gap-2 mt-4">
              <span className="text-green-400">➜</span>
              <span className="text-blue-400">~</span>
              <span className="text-white animate-pulse">_</span>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
