"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { AlertTriangle, Check, Loader2, Pencil, X } from "lucide-react";
import { toast } from "sonner";
import { apiClient, ApiError } from "@/lib/api-client";

// ── Types (mirrors app/engines/form_mapping/schema.py) ──────────────────────

export interface FieldSource {
  document_id: string;
  document_class: string | null;
  extraction_method: string | null;
  extractor_name: string | null;
  confidence: number;
  raw_value: string | null;
}

export interface MappedField {
  value: unknown;
  status: "FOUND" | "CONFLICT" | "NOT_FOUND";
  confidence: number;
  reason: string | null;
  source: FieldSource | null;
  alternatives: FieldSource[];
}

export interface ClaimOpeningForm {
  [key: string]: MappedField | ClaimOpeningForm[] | ClaimOpeningForm | string[];
}

interface ValidationIssue {
  severity: string;
  description: string;
  created_at: string | null;
}

interface ValidationReport {
  claim_id: string;
  decision?: string;
  composite_confidence?: number;
  decided_at?: string | null;
  issues?: ValidationIssue[];
  message?: string;
}

const SEVERITY_RANK: Record<string, number> = {
  BLOCKER: 5,
  CRITICAL: 4,
  ERROR: 3,
  WARNING: 2,
  INFO: 1,
};

const SEVERITY_STYLE: Record<string, string> = {
  BLOCKER: "bg-red-600/10 text-red-600",
  CRITICAL: "bg-red-500/10 text-red-500",
  ERROR: "bg-orange-500/10 text-orange-500",
  WARNING: "bg-amber-500/10 text-amber-500",
  INFO: "bg-blue-500/10 text-blue-500",
};

const isMappedField = (v: unknown): v is MappedField =>
  typeof v === "object" && v !== null && "status" in (v as object) && "confidence" in (v as object);

// ── Field-level UI ────────────────────────────────────────────────────────

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    confidence >= 0.85
      ? "bg-green-500/10 text-green-600"
      : confidence >= 0.5
      ? "bg-amber-500/10 text-amber-600"
      : "bg-red-500/10 text-red-600";
  return (
    <Badge className={color} variant="secondary">
      {pct}%
    </Badge>
  );
}

function StatusBadge({ status }: { status: MappedField["status"] }) {
  if (status === "FOUND") {
    return (
      <Badge className="bg-green-500/10 text-green-600" variant="secondary">
        Trouvé
      </Badge>
    );
  }
  if (status === "CONFLICT") {
    return (
      <Badge className="bg-amber-500/10 text-amber-600" variant="secondary">
        Conflit
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-muted-foreground">
      Non trouvé
    </Badge>
  );
}

function FieldRow({
  path,
  label,
  field,
  onCorrect,
}: {
  path: string;
  label: string;
  field: MappedField;
  onCorrect: (path: string, value: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  const displayValue =
    field.value === null || field.value === undefined || field.value === ""
      ? "—"
      : typeof field.value === "boolean"
      ? field.value
        ? "Oui"
        : "Non"
      : String(field.value);

  const startEditing = () => {
    setDraft(field.value === null || field.value === undefined ? "" : String(field.value));
    setEditing(true);
  };

  const save = async () => {
    setSaving(true);
    try {
      await onCorrect(path, draft);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="py-2 border-b border-border/50 last:border-0">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-xs text-muted-foreground">{label}</div>
          {editing ? (
            <div className="flex items-center gap-2 mt-1">
              <Input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                className="h-8"
                autoFocus
              />
              <Button size="icon" variant="ghost" className="h-8 w-8" onClick={save} disabled={saving}>
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4 text-green-600" />}
              </Button>
              <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setEditing(false)} disabled={saving}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <div className="text-sm font-medium truncate group flex items-center gap-2">
              {displayValue}
              <button
                onClick={startEditing}
                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-foreground transition-opacity"
                aria-label={`Corriger ${label}`}
              >
                <Pencil className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
        {!editing && (
          <div className="flex items-center gap-2 shrink-0">
            {field.status !== "NOT_FOUND" && <ConfidenceBadge confidence={field.confidence} />}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <StatusBadge status={field.status} />
                </TooltipTrigger>
                <TooltipContent>
                  {field.status === "NOT_FOUND" ? (
                    <p className="max-w-xs text-xs">{field.reason}</p>
                  ) : (
                    <p className="max-w-xs text-xs">
                      Source : {field.source?.extractor_name} ({field.source?.extraction_method})
                    </p>
                  )}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}
      </div>

      {field.status === "CONFLICT" && field.alternatives.length > 0 && (
        <div className="mt-1 pl-1 border-l-2 border-amber-500/30 space-y-1">
          <p className="text-xs text-muted-foreground">
            Valeur retenue : source la plus fiable. Alternative(s) écartée(s) :
          </p>
          {field.alternatives.map((alt, i) => (
            <p key={i} className="text-xs text-muted-foreground">
              «{alt.raw_value}» — doc {alt.document_id.slice(0, 8)} · {alt.extractor_name} ·{" "}
              {Math.round(alt.confidence * 100)}%
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

interface LabeledField {
  path: string;
  label: string;
  field: MappedField;
}

function FormSection({
  title,
  entries,
  onCorrect,
}: {
  title: string;
  entries: LabeledField[];
  onCorrect: (path: string, value: string) => Promise<void>;
}) {
  if (entries.length === 0) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {entries.map(({ path, label, field }) => (
          <FieldRow key={path} path={path} label={label} field={field} onCorrect={onCorrect} />
        ))}
      </CardContent>
    </Card>
  );
}

// ── Anomalies panel ──────────────────────────────────────────────────────

function AnomaliesPanel({ report }: { report: ValidationReport | null }) {
  if (!report || report.message) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" /> Anomalies détectées
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Aucune validation exécutée pour l&apos;instant.</p>
        </CardContent>
      </Card>
    );
  }

  const issues = [...(report.issues ?? [])].sort(
    (a, b) => (SEVERITY_RANK[b.severity] ?? 0) - (SEVERITY_RANK[a.severity] ?? 0)
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-muted-foreground" /> Anomalies détectées ({issues.length})
        </CardTitle>
        {report.decision && (
          <Badge
            className={
              report.decision === "STP_APPROVED"
                ? "bg-green-500/10 text-green-600"
                : report.decision === "REJECTED"
                ? "bg-red-500/10 text-red-600"
                : "bg-amber-500/10 text-amber-600"
            }
            variant="secondary"
          >
            {report.decision}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-2">
        {issues.length === 0 ? (
          <p className="text-sm text-muted-foreground">Aucune anomalie détectée sur les documents fournis.</p>
        ) : (
          issues.map((issue, i) => (
            <div key={i} className="flex items-start gap-2 text-sm">
              <Badge className={SEVERITY_STYLE[issue.severity] ?? ""} variant="secondary">
                {issue.severity}
              </Badge>
              <span className="flex-1">{issue.description}</span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────

export const TOP_LEVEL_LABELS: Record<string, string> = {
  numero_police: "N° de police",
  nom_souscripteur: "Nom du souscripteur",
  prenom_souscripteur: "Prénom du souscripteur",
  numero_cin_souscripteur: "CIN du souscripteur",
  numero_immatriculation: "Immatriculation",
  categorie_vehicule: "Catégorie du véhicule",
  date_effet_contrat: "Date d'effet du contrat",
  date_echeance_contrat: "Date d'échéance du contrat",
  conducteur_est_souscripteur: "Conducteur = souscripteur",
  numero_pv: "N° de PV",
  pays_survenance: "Pays de survenance",
  lieu_survenance: "Lieu de survenance",
  juridiction: "Juridiction",
  date_survenance: "Date de survenance",
  heure_survenance: "Heure de survenance",
  victimes_blessees: "Victimes blessées",
  victimes_decedees: "Victimes décédées",
  autorite: "Autorité",
  circonscription: "Circonscription",
  reference_cabinet: "Référence cabinet",
  degats_materiels_partie_adverse: "Dégâts matériels (partie adverse)",
  cas_bareme: "Cas du barème",
  circonstances_accident: "Circonstances de l'accident",
  responsabilite_pct: "Responsabilité (%)",
  description: "Description",
  procedure_judiciaire: "Procédure judiciaire",
  sinistre_suspicieux: "Sinistre suspicieux",
  avocat_adverse: "Avocat adverse",
};

export const CONDUCTEUR_LABELS: Record<string, string> = {
  nom: "Nom", prenom: "Prénom", numero_cin: "CIN", date_naissance: "Date de naissance",
  sexe: "Sexe", date_permis: "Date du permis", categorie_permis: "Catégorie du permis",
  numero_permis: "N° du permis", qualite: "Qualité",
};

export const PARTIE_ADVERSE_LABELS: Record<string, string> = {
  marque_vehicule: "Marque du véhicule", type_immatriculation: "Type d'immatriculation",
  immatriculation: "Immatriculation", compagnie_adverse: "Compagnie adverse", prenom: "Prénom",
  nom: "Nom", numero_police: "N° de police", numero_attestation: "N° d'attestation",
  numero_sinistre: "N° de sinistre", responsabilite: "Responsabilité",
};

const VICTIME_LABELS: Record<string, string> = {
  nature_victime: "Nature", numero_cin: "CIN", nom: "Nom", prenom: "Prénom",
  numero_telephone: "Téléphone", qualite_victime: "Qualité", classe: "Classe",
  type_procedure_recommandee: "Procédure recommandée", type_profession: "Profession",
  accident_travail: "Accident du travail", disponibilite_itt: "ITT", itt_jours: "Jours d'ITT",
  opposition: "Opposition", ville: "Ville", adresse: "Adresse", exclue_garantie: "Exclu de garantie",
};

function labelFor(map: Record<string, string>, key: string): string {
  return map[key] ?? key;
}

export function ClaimReviewPanel({ claimId }: { claimId: string }) {
  const [form, setForm] = useState<ClaimOpeningForm | null>(null);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [formData, validationData] = await Promise.all([
        apiClient.get<ClaimOpeningForm>(`/claims/${claimId}/documents/opening-form`),
        apiClient.get<ValidationReport>(`/claims/${claimId}/validation`),
      ]);
      setForm(formData);
      setValidation(validationData);
    } catch {
      toast.error("Impossible de charger la revue du sinistre");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimId]);

  const handleCorrect = async (fieldPath: string, value: string) => {
    try {
      const updated = await apiClient.patch<ClaimOpeningForm>(
        `/claims/${claimId}/documents/opening-form`,
        { field_path: fieldPath, value }
      );
      setForm(updated);
      toast.success("Champ corrigé");
    } catch (err) {
      const message =
        err instanceof ApiError ? err.data?.detail || "Échec de la correction." : "Serveur injoignable.";
      toast.error(typeof message === "string" ? message : "Échec de la correction.");
      throw err;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!form) {
    return <p className="text-sm text-muted-foreground">Impossible de charger le formulaire.</p>;
  }

  const toLabeledFields = (
    entries: [string, MappedField][],
    map: Record<string, string>,
    pathPrefix = ""
  ): LabeledField[] =>
    entries.map(([key, field]) => ({
      path: pathPrefix ? `${pathPrefix}.${key}` : key,
      label: labelFor(map, key),
      field,
    }));

  const conducteurEntries = toLabeledFields(
    form.conducteur
      ? Object.entries(form.conducteur).filter((e): e is [string, MappedField] => isMappedField(e[1]))
      : [],
    CONDUCTEUR_LABELS,
    "conducteur"
  );
  const partieAdverseEntries = toLabeledFields(
    form.partie_adverse
      ? Object.entries(form.partie_adverse).filter((e): e is [string, MappedField] => isMappedField(e[1]))
      : [],
    PARTIE_ADVERSE_LABELS,
    "partie_adverse"
  );
  const skipKeys = new Set(["conducteur", "partie_adverse", "victimes", "fraud_indicators"]);
  const topLevelEntries = toLabeledFields(
    Object.entries(form)
      .filter(([k]) => !skipKeys.has(k))
      .filter((e): e is [string, MappedField] => isMappedField(e[1])),
    TOP_LEVEL_LABELS
  );
  const victims: ClaimOpeningForm[] = Array.isArray(form.victimes) ? (form.victimes as ClaimOpeningForm[]) : [];

  return (
    <div className="space-y-4">
      <AnomaliesPanel report={validation} />
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Police & souscripteur / Sinistre</CardTitle>
          </CardHeader>
          <CardContent>
            {topLevelEntries.map(({ path, label, field }) => (
              <FieldRow key={path} path={path} label={label} field={field} onCorrect={handleCorrect} />
            ))}
          </CardContent>
        </Card>
        <div className="space-y-4">
          <FormSection title="Conducteur" entries={conducteurEntries} onCorrect={handleCorrect} />
          <FormSection title="Partie adverse" entries={partieAdverseEntries} onCorrect={handleCorrect} />
        </div>
      </div>

      {victims.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Victimes ({victims.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {victims.map((victim, idx) => (
              <div key={idx} className="border rounded-md p-3">
                <p className="text-xs text-muted-foreground mb-2">
                  Victime {idx + 1} — correction non disponible pour cette version (liste)
                </p>
                {Object.entries(victim)
                  .filter((e): e is [string, MappedField] => isMappedField(e[1]))
                  .map(([key, field]) => (
                    <div key={key} className="py-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground text-xs">{labelFor(VICTIME_LABELS, key)}</span>
                      <span className="flex items-center gap-2">
                        {field.value !== null && field.value !== undefined ? String(field.value) : "—"}
                        {field.status !== "NOT_FOUND" && <ConfidenceBadge confidence={field.confidence} />}
                      </span>
                    </div>
                  ))}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
