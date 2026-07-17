"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FlaskConical, Bot, Beaker, Play, Save, RotateCcw, Brain, Layers } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface Agent {
  name: string;
  model_name: string;
  role: string;
  allowed_tools: string[];
  max_context_tokens: number;
  temperature: number;
  specialty: string;
  autonomy_level: string;
}

export default function AILaboratoryPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [promptText, setPromptText] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        setLoading(true);
        const data = await apiClient.get<Agent[]>("/agentic-ai/agents");
        setAgents(data || []);
        if (data && data.length > 0) {
          setSelectedAgent(data[0]);
        }
      } catch (err) {
        console.error("Failed to fetch agents", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAgents();
  }, []);

  const handleFetchPrompt = async (agentName: string) => {
    try {
      const data = await apiClient.get<any>(`/agentic-ai/prompts/${agentName}`);
      setPromptText(data?.prompt || "");
    } catch (err) {
      setPromptText("");
    }
  };

  useEffect(() => {
    if (selectedAgent) {
      handleFetchPrompt(selectedAgent.name);
    }
  }, [selectedAgent]);

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading AI Laboratory...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Laboratory</h1>
          <p className="text-muted-foreground mt-1">Prompt engineering, fine-tuning, and model evaluation.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
            <FlaskConical className="w-4 h-4" /> Run Evaluation
          </Button>
          <Button className="gap-2">
            <Play className="w-4 h-4" /> Start Experiment
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-12">
        <div className="md:col-span-3 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Available Agents</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="flex flex-col divide-y divide-border">
                {agents.map((agent) => (
                  <button
                    key={agent.name}
                    onClick={() => setSelectedAgent(agent)}
                    className={`flex items-center gap-3 p-3 text-left transition-colors hover:bg-muted/50 ${
                      selectedAgent?.name === agent.name ? "bg-muted/80 border-l-2 border-primary" : ""
                    }`}
                  >
                    <div className="p-2 bg-secondary rounded-md">
                      <Bot className="w-4 h-4 text-secondary-foreground" />
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <div className="text-sm font-medium truncate">{agent.name}</div>
                      <div className="text-xs text-muted-foreground truncate">{agent.role}</div>
                    </div>
                  </button>
                ))}
                {agents.length === 0 && (
                  <div className="p-4 text-center text-sm text-muted-foreground">
                    No agents available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-9 space-y-4">
          {selectedAgent ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-primary" /> Model Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Base Model</div>
                      <div className="font-medium">{selectedAgent.model_name}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Temperature</div>
                      <div className="font-medium">{selectedAgent.temperature}</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Context Window</div>
                      <div className="font-medium">{selectedAgent.max_context_tokens.toLocaleString()} tk</div>
                    </div>
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Autonomy</div>
                      <div className="font-medium capitalize">{selectedAgent.autonomy_level.toLowerCase()}</div>
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t border-border">
                    <div className="text-xs text-muted-foreground mb-2">Available Tools</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedAgent.allowed_tools.map((tool, idx) => (
                        <span key={idx} className="inline-flex items-center gap-1.5 rounded-md bg-muted px-2 py-1 text-xs font-medium">
                          <Layers className="w-3 h-3 text-muted-foreground" /> {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Beaker className="w-5 h-5 text-blue-500" /> Prompt Engineering Workspace
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Modify the system prompt to adjust behavior and reasoning capabilities.
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleFetchPrompt(selectedAgent.name)}>
                      <RotateCcw className="w-4 h-4 mr-2" /> Reset
                    </Button>
                    <Button size="sm">
                      <Save className="w-4 h-4 mr-2" /> Save Prompt
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Textarea 
                    value={promptText}
                    onChange={(e) => setPromptText(e.target.value)}
                    placeholder="Enter the system prompt instructions here. Variables can be injected via {{var_name}}."
                    className="min-h-[300px] font-mono text-sm leading-relaxed bg-muted/30"
                  />
                  {promptText === "" && (
                    <p className="text-xs text-amber-500 mt-2">
                      Warning: No active prompt found for this agent in the database. Using fallback behavior.
                    </p>
                  )}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="h-full min-h-[400px] flex items-center justify-center border-dashed border-2 bg-transparent text-center p-12">
              <div className="flex flex-col items-center space-y-4">
                <div className="p-4 bg-muted rounded-full">
                  <Bot className="w-8 h-8 text-muted-foreground" />
                </div>
                <h3 className="text-xl font-medium tracking-tight">Select an Agent</h3>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  Choose an AI agent from the sidebar to inspect its configuration and edit its prompt instructions.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
