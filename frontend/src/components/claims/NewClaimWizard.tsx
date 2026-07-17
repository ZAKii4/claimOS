"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, FileText, Loader2, Upload, XCircle } from "lucide-react";
import { toast } from "sonner";
import { apiClient, ApiError } from "@/lib/api-client";
import { ClaimReviewPanel } from "@/components/claims/ClaimReviewPanel";
import { ManualEntryForm } from "@/components/claims/ManualEntryForm";

interface ClaimType {
  id: string;
  code: string;
  label_fr: string;
}

const DOCUMENT_ROLES = [
  { value: "OWN_VEHICLE", label: "Véhicule assuré" },
  { value: "ADVERSE_VEHICLE", label: "Véhicule adverse" },
  { value: "POLICY_HOLDER", label: "Souscripteur" },
  { value: "VICTIM", label: "Victime" },
  { value: "ACCIDENT_REPORT", label: "Constat / PV" },
];

type FileStatus = "pending" | "uploading" | "processing" | "done" | "error";

interface PendingFile {
  id: string;
  file: File;
  role: string;
  status: FileStatus;
  error?: string;
}

type Step = "details" | "upload" | "review";

export function NewClaimWizard({
  open,
  onOpenChange,
  claimTypes,
  onClaimCreated,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  claimTypes: ClaimType[];
  onClaimCreated: () => void;
}) {
  const [step, setStep] = useState<Step>("details");
  // Two ways to populate a claim's opening form (see
  // docs/COURS_01_DECISIONS_ARCHITECTURE.md §5): upload documents for
  // automatic extraction, or fill the form by hand when no paperwork is
  // available yet. Not mutually exclusive — an operator can switch and do
  // both over time — but the wizard only asks once, up front.
  const [entryMode, setEntryMode] = useState<"upload" | "manual">("upload");

  const [externalRef, setExternalRef] = useState("");
  const [claimTypeId, setClaimTypeId] = useState("");
  const [dateOfLoss, setDateOfLoss] = useState("");
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [claimId, setClaimId] = useState<string | null>(null);
  const [files, setFiles] = useState<PendingFile[]>([]);
  const [processing, setProcessing] = useState(false);

  const reset = () => {
    setStep("details");
    setExternalRef("");
    setClaimTypeId("");
    setDateOfLoss("");
    setFormError(null);
    setClaimId(null);
    setFiles([]);
  };

  const close = () => {
    onOpenChange(false);
    onClaimCreated();
    reset();
  };

  const handleCreateClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!externalRef.trim() || !claimTypeId || !dateOfLoss) {
      setFormError("Tous les champs sont requis.");
      return;
    }
    setCreating(true);
    setFormError(null);
    try {
      const claim = await apiClient.post<{ id: string }>("/claims", {
        external_ref: externalRef.trim(),
        claim_type_id: claimTypeId,
        date_of_loss: dateOfLoss,
      });
      setClaimId(claim.id);
      setStep("upload");
    } catch (err) {
      const message =
        err instanceof ApiError ? err.data?.detail || "Échec de la création du sinistre." : "Serveur injoignable.";
      setFormError(typeof message === "string" ? message : "Échec de la création du sinistre.");
    } finally {
      setCreating(false);
    }
  };

  const addFiles = (selected: FileList | null) => {
    if (!selected) return;
    const next: PendingFile[] = Array.from(selected).map((file) => ({
      id: `${file.name}-${file.size}-${Math.random().toString(36).slice(2)}`,
      file,
      role: "",
      status: "pending",
    }));
    setFiles((prev) => [...prev, ...next]);
  };

  const setFileRole = (id: string, role: string) => {
    setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, role } : f)));
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const processFiles = async () => {
    if (!claimId || files.length === 0) return;
    setProcessing(true);

    // Sequential on purpose: each upload can take ~60-70s (real LLM
    // extraction call per document) — running them in parallel would pile
    // up that latency against the same backend/Ollama instance rather than
    // actually speeding anything up, and makes per-file progress harder to
    // read. One file failing does not stop the others.
    for (const f of files) {
      setFiles((prev) => prev.map((p) => (p.id === f.id ? { ...p, status: "uploading" } : p)));
      try {
        const formData = new FormData();
        formData.append("file", f.file);
        if (f.role) formData.append("document_role", f.role);

        setFiles((prev) => prev.map((p) => (p.id === f.id ? { ...p, status: "processing" } : p)));
        // One upload can contain several distinct scanned documents (e.g. a
        // police PV followed by an insurance attestation) — the backend now
        // splits it into one sub-document per detected type.
        const created = await apiClient.postForm<{ document_type: string }[]>(
          `/claims/${claimId}/documents`,
          formData
        );
        if (created.length > 1) {
          toast.info(`${f.file.name} : ${created.length} documents détectés (${created.map((d) => d.document_type).join(", ")})`);
        }

        setFiles((prev) => prev.map((p) => (p.id === f.id ? { ...p, status: "done" } : p)));
      } catch (err) {
        const message =
          err instanceof ApiError ? err.data?.detail || "Échec du traitement." : "Serveur injoignable.";
        setFiles((prev) =>
          prev.map((p) =>
            p.id === f.id
              ? { ...p, status: "error", error: typeof message === "string" ? message : "Échec du traitement." }
              : p
          )
        );
      }
    }

    setProcessing(false);
    const failedCount = files.filter((f) => f.status === "error").length;
    if (failedCount > 0) {
      toast.warning(`${failedCount} document(s) en échec — les autres ont bien été traités`);
    } else {
      toast.success("Tous les documents ont été traités");
    }
    setStep("review");
  };

  return (
    <Dialog open={open} onOpenChange={(next) => (next ? onOpenChange(next) : close())}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nouveau sinistre</DialogTitle>
          <DialogDescription>
            {step === "details" && "Étape 1/3 — Informations du dossier"}
            {step === "upload" && "Étape 2/3 — Documents du dossier"}
            {step === "review" && "Étape 3/3 — Revue des données extraites"}
          </DialogDescription>
        </DialogHeader>

        {step === "details" && (
          <form onSubmit={handleCreateClaim} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Référence externe</label>
              <Input
                value={externalRef}
                onChange={(e) => setExternalRef(e.target.value)}
                placeholder="CLM-2026-0001"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Type de sinistre</label>
              <select
                value={claimTypeId}
                onChange={(e) => setClaimTypeId(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Sélectionner un type...</option>
                {claimTypes.map((ct) => (
                  <option key={ct.id} value={ct.id}>
                    {ct.label_fr} ({ct.code})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Date du sinistre</label>
              <Input type="date" value={dateOfLoss} onChange={(e) => setDateOfLoss(e.target.value)} />
            </div>
            {formError && (
              <p className="text-sm text-red-600" role="alert">
                {formError}
              </p>
            )}
            <DialogFooter>
              <Button type="submit" disabled={creating}>
                {creating ? "Création..." : "Créer et ajouter des documents"}
              </Button>
            </DialogFooter>
          </form>
        )}

        {step === "upload" && (
          <div className="space-y-4">
            <div className="flex gap-2 border-b pb-3">
              <Button
                type="button"
                variant={entryMode === "upload" ? "default" : "outline"}
                size="sm"
                onClick={() => setEntryMode("upload")}
              >
                <Upload className="mr-2 h-4 w-4" /> Uploader des documents
              </Button>
              <Button
                type="button"
                variant={entryMode === "manual" ? "default" : "outline"}
                size="sm"
                onClick={() => setEntryMode("manual")}
              >
                Saisie manuelle
              </Button>
            </div>

            {entryMode === "manual" && claimId && (
              <ManualEntryForm claimId={claimId} onSubmitted={() => setStep("review")} />
            )}

            {entryMode === "upload" && (
            <>
            <div className="space-y-2">
              <label className="text-sm font-medium">Ajouter des fichiers</label>
              <input
                type="file"
                multiple
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(e) => addFiles(e.target.files)}
                disabled={processing}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm file:mr-3 file:border-0 file:bg-transparent file:text-sm file:font-medium"
              />
            </div>

            {files.length > 0 && (
              <div className="space-y-2">
                {files.map((f) => (
                  <div key={f.id} className="flex items-center gap-3 border rounded-md p-2">
                    <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                    <span className="text-sm truncate flex-1">{f.file.name}</span>
                    <select
                      value={f.role}
                      onChange={(e) => setFileRole(f.id, e.target.value)}
                      disabled={f.status !== "pending"}
                      className="h-8 rounded-md border border-input bg-background px-2 text-xs"
                    >
                      <option value="">Rôle non spécifié</option>
                      {DOCUMENT_ROLES.map((r) => (
                        <option key={r.value} value={r.value}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                    <FileStatusBadge status={f.status} error={f.error} />
                    {f.status === "pending" && (
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => removeFile(f.id)}>
                        <XCircle className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setStep("review")} disabled={processing}>
                Passer (sans documents)
              </Button>
              <Button onClick={processFiles} disabled={files.length === 0 || processing}>
                {processing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Traitement en cours...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" /> Traiter {files.length || ""} document(s)
                  </>
                )}
              </Button>
            </DialogFooter>
            </>
            )}
          </div>
        )}

        {step === "review" && claimId && (
          <div className="space-y-4">
            <ClaimReviewPanel claimId={claimId} />
            <DialogFooter>
              <Button onClick={close}>Terminer</Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function FileStatusBadge({ status, error }: { status: FileStatus; error?: string }) {
  switch (status) {
    case "pending":
      return (
        <Badge variant="outline" className="text-muted-foreground">
          En attente
        </Badge>
      );
    case "uploading":
      return (
        <Badge className="bg-blue-500/10 text-blue-600" variant="secondary">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" /> Envoi
        </Badge>
      );
    case "processing":
      return (
        <Badge className="bg-blue-500/10 text-blue-600" variant="secondary">
          <Loader2 className="mr-1 h-3 w-3 animate-spin" /> OCR + IA
        </Badge>
      );
    case "done":
      return (
        <Badge className="bg-green-500/10 text-green-600" variant="secondary">
          <CheckCircle2 className="mr-1 h-3 w-3" /> Terminé
        </Badge>
      );
    case "error":
      return (
        <Badge className="bg-red-500/10 text-red-600" variant="secondary" title={error}>
          <XCircle className="mr-1 h-3 w-3" /> Erreur
        </Badge>
      );
  }
}
