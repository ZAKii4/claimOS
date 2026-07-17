"use client";

/**
 * Triggers and displays the 6-agent collaboration pipeline (OCR Supervisor,
 * Extraction, Fraud, Legal, Decision, Supervisor agents — see
 * backend/app/agents/modules/ and docs/COURS_04_AGENTS.md) for a claim.
 *
 * This is a distinct step from document ingestion: it reasons over a
 * claim's already-persisted, fused opening form (from uploads and/or manual
 * entry) rather than re-running OCR/extraction — see
 * docs/COURS_05_ORCHESTRATION.md. Not run automatically; an operator
 * triggers it explicitly once the dossier has some data.
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Bot, Loader2, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { apiClient, ApiError } from "@/lib/api-client";

interface AgentResult {
  status: "SUCCESS" | "FAILED" | "SKIPPED" | null;
  confidence: number;
  execution_time_ms: number;
  artifacts: Record<string, unknown>;
  messages: string[];
}

interface SupervisorSummary {
  final_decision: string;
  overridden: boolean;
  override_reason: string | null;
  failed_agents: string[];
}

interface AgentRunResult {
  status: string;
  context: {
    validation_report: { source: string; compliant: boolean; issues: string[]; llm_enriched: boolean } | Record<string, never>;
    decision: { decision: string; reason: string; confidence: number } | Record<string, never>;
    metadata: {
      fraud_score?: number;
      extraction_completeness?: number;
      supervisor_summary?: SupervisorSummary;
    };
  };
  agent_results: Record<string, AgentResult | null>;
}

const AGENT_LABELS: Record<string, string> = {
  ocr_supervisor: "OCR Agent",
  extraction_agent: "Extraction Agent",
  fraud_agent: "Fraud Agent",
  legal_agent: "Legal Agent",
  decision_agent: "Decision Agent",
  supervisor_agent: "Supervisor Agent",
};
const AGENT_ORDER = Object.keys(AGENT_LABELS);

const DECISION_STYLE: Record<string, string> = {
  AUTO_APPROVED: "bg-green-500/10 text-green-600",
  HUMAN_REVIEW: "bg-amber-500/10 text-amber-600",
  FRAUD_REVIEW: "bg-red-500/10 text-red-600",
  REQUEST_MORE_DOCUMENTS: "bg-blue-500/10 text-blue-600",
};

function AgentStatusBadge({ status }: { status: AgentResult["status"] }) {
  if (status === "SUCCESS") return <Badge className="bg-green-500/10 text-green-600" variant="secondary">Exécuté</Badge>;
  if (status === "FAILED") return <Badge className="bg-red-500/10 text-red-600" variant="secondary">Échec</Badge>;
  return <Badge variant="outline" className="text-muted-foreground">Ignoré</Badge>;
}

export function AgentCollaborationPanel({ claimId }: { claimId: string }) {
  const [result, setResult] = useState<AgentRunResult | null>(null);
  const [running, setRunning] = useState(false);

  const run = async () => {
    setRunning(true);
    try {
      const data = await apiClient.post<AgentRunResult>(`/claims/${claimId}/agents/run`, {});
      setResult(data);
      toast.success("Analyse multi-agents terminée");
    } catch (err) {
      const message =
        err instanceof ApiError ? err.data?.detail || "Échec de l'analyse." : "Serveur injoignable.";
      toast.error(typeof message === "string" ? message : "Échec de l'analyse.");
    } finally {
      setRunning(false);
    }
  };

  const summary = result?.context.metadata.supervisor_summary;
  const decision = summary?.final_decision ?? result?.context.decision?.decision;
  const fraudScore = result?.context.metadata.fraud_score;
  const validation = result?.context.validation_report;
  const completeness = result?.context.metadata.extraction_completeness;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Bot className="h-4 w-4 text-muted-foreground" /> Collaboration multi-agents
          </CardTitle>
          <Button onClick={run} disabled={running} size="sm">
            {running ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyse en cours...
              </>
            ) : (
              "Lancer l'analyse IA"
            )}
          </Button>
        </CardHeader>
        <CardContent>
          {!result ? (
            <p className="text-sm text-muted-foreground">
              Analyse un dossier déjà rempli (par upload ou saisie manuelle) : score de fraude,
              conformité légale, et une recommandation de décision explicable — voir
              docs/COURS_04_AGENTS.md.
            </p>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                {decision && (
                  <Badge className={DECISION_STYLE[decision] ?? ""} variant="secondary">
                    {decision}
                  </Badge>
                )}
                {typeof fraudScore === "number" && (
                  <span className="text-sm text-muted-foreground">
                    Score de fraude : <strong>{Math.round(fraudScore * 100)}%</strong>
                  </span>
                )}
                {typeof completeness === "number" && (
                  <span className="text-sm text-muted-foreground">
                    Complétude des données : <strong>{Math.round(completeness * 100)}%</strong>
                  </span>
                )}
              </div>

              {summary?.overridden && (
                <div className="flex items-start gap-2 text-sm bg-amber-500/10 text-amber-700 rounded-md p-3">
                  <ShieldAlert className="h-4 w-4 mt-0.5 shrink-0" />
                  <span>{summary.override_reason}</span>
                </div>
              )}

              {validation && "issues" in validation && validation.issues.length > 0 && (
                <div className="space-y-1">
                  <p className="text-sm font-medium flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500" /> Incohérences légales
                  </p>
                  {validation.issues.map((issue, i) => (
                    <p key={i} className="text-xs text-muted-foreground pl-6">
                      {issue}
                    </p>
                  ))}
                </div>
              )}

              <div className="grid gap-2 sm:grid-cols-2">
                {AGENT_ORDER.map((agentId) => {
                  const agentResult = result.agent_results[agentId];
                  return (
                    <div
                      key={agentId}
                      className="flex items-center justify-between border rounded-md px-3 py-2"
                    >
                      <div>
                        <p className="text-sm font-medium">{AGENT_LABELS[agentId]}</p>
                        {agentResult?.messages?.[0] && (
                          <p className="text-xs text-muted-foreground truncate max-w-xs">
                            {agentResult.messages[0]}
                          </p>
                        )}
                      </div>
                      <AgentStatusBadge status={agentResult?.status ?? null} />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
