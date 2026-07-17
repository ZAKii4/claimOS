"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Network, Play, Settings2, Clock, GitCommit, Search, Plus } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  created_at: string;
  steps_count: number;
  trigger_type: string;
}

export default function WorkflowStudioPage() {
  const [definitions, setDefinitions] = useState<WorkflowDefinition[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDefinitions = async () => {
      try {
        setLoading(true);
        const data = await apiClient.get<WorkflowDefinition[]>("/workflows/definitions");
        setDefinitions(data);
      } catch (err) {
        console.error("Failed to fetch workflow definitions", err);
        setDefinitions([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDefinitions();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading Workflow Engine...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workflow Studio</h1>
          <p className="text-muted-foreground mt-1">Design, orchestrate, and monitor autonomous AI pipelines.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <Search className="w-4 h-4" /> Browse Templates
          </Button>
          <Button className="gap-2">
            <Plus className="w-4 h-4" /> Create Workflow
          </Button>
        </div>
      </div>

      <div className="grid gap-6">
        {definitions && definitions.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {definitions.map((workflow) => (
              <Card key={workflow.id} className="flex flex-col">
                <CardHeader>
                  <div className="flex justify-between items-start mb-2">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <Network className="w-5 h-5 text-primary" />
                    </div>
                    <span className="inline-flex items-center rounded-md bg-secondary px-2 py-1 text-xs font-medium text-secondary-foreground">
                      v{workflow.version}
                    </span>
                  </div>
                  <CardTitle className="text-lg">{workflow.name}</CardTitle>
                  <CardDescription className="line-clamp-2">{workflow.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  <div className="flex gap-4 text-sm text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <GitCommit className="w-4 h-4" />
                      {workflow.steps_count} Steps
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-4 h-4" />
                      {workflow.trigger_type}
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="pt-4 border-t flex gap-2">
                  <Button variant="default" className="w-full gap-2">
                    <Play className="w-4 h-4" /> Run Instance
                  </Button>
                  <Button variant="outline" size="icon">
                    <Settings2 className="w-4 h-4" />
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="border-dashed border-2 bg-transparent text-center p-12">
            <CardContent className="flex flex-col items-center justify-center space-y-4">
              <div className="p-4 bg-muted rounded-full">
                <Network className="w-8 h-8 text-muted-foreground" />
              </div>
              <div className="space-y-1">
                <h3 className="text-xl font-medium tracking-tight">No Workflows Deployed</h3>
                <p className="text-sm text-muted-foreground max-w-md mx-auto">
                  There are currently no active workflow definitions registered in the engine. Create a new workflow or install a template from the marketplace.
                </p>
              </div>
              <Button className="mt-4 gap-2">
                <Plus className="w-4 h-4" /> Create New Workflow
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
