"use client";

/**
 * Bulk manual entry for a claim's opening form — the "no document" path,
 * alternative to uploading a scanned dossier. Every field maps 1:1 to a
 * dotted path on the backend's ClaimOpeningForm (see
 * backend/app/engines/form_mapping/schema.py) and is submitted in one
 * request to POST /claims/{claimId}/documents/opening-form/manual
 * (DocumentService.submit_manual_fields — see
 * docs/COURS_03_SAISIE_MANUELLE.md for why this is a bulk version of the
 * same field_overrides mechanism the inline correction UI already uses).
 *
 * Victim entries (victimes.<index>.*) are intentionally not included here:
 * the backend doesn't support list-path corrections yet (same limit
 * ClaimReviewPanel's victim block already documents), so this form only
 * covers scalar + nested-object fields.
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { apiClient, ApiError } from "@/lib/api-client";
import {
  TOP_LEVEL_LABELS,
  CONDUCTEUR_LABELS,
  PARTIE_ADVERSE_LABELS,
  type ClaimOpeningForm,
} from "@/components/claims/ClaimReviewPanel";

type FieldKind = "text" | "date" | "number" | "boolean";

// Mirrors the value types LLMFieldExtractor declares server-side
// (SCALAR_FIELD_SPECS in llm_field_extractor.py) so the input widget matches
// what the backend will actually coerce the value into.
const FIELD_KIND: Record<string, FieldKind> = {
  date_survenance: "date",
  date_effet_contrat: "date",
  date_echeance_contrat: "date",
  responsabilite_pct: "number",
  victimes_blessees: "boolean",
  victimes_decedees: "boolean",
  conducteur_est_souscripteur: "boolean",
  sinistre_suspicieux: "boolean",
};
const CONDUCTEUR_FIELD_KIND: Record<string, FieldKind> = {
  date_naissance: "date",
  date_permis: "date",
};

const SKIP_TOP_LEVEL = new Set(["conducteur", "partie_adverse", "victimes", "fraud_indicators"]);

function BooleanSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
    >
      <option value="">—</option>
      <option value="true">Oui</option>
      <option value="false">Non</option>
    </select>
  );
}

function SectionInputs({
  prefix,
  labels,
  kinds,
  values,
  onChange,
}: {
  prefix: string;
  labels: Record<string, string>;
  kinds: Record<string, FieldKind>;
  values: Record<string, string>;
  onChange: (path: string, value: string) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Object.entries(labels).map(([key, label]) => {
        const path = prefix ? `${prefix}.${key}` : key;
        const kind = kinds[key] ?? "text";
        return (
          <div key={path} className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground">{label}</label>
            {kind === "boolean" ? (
              <BooleanSelect
                value={values[path] ?? ""}
                onChange={(v) => onChange(path, v)}
              />
            ) : (
              <Input
                type={kind === "date" ? "date" : kind === "number" ? "number" : "text"}
                value={values[path] ?? ""}
                onChange={(e) => onChange(path, e.target.value)}
                className="h-9"
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function ManualEntryForm({
  claimId,
  onSubmitted,
}: {
  claimId: string;
  onSubmitted: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  const setField = (path: string, value: string) =>
    setValues((prev) => ({ ...prev, [path]: value }));

  const topLevelLabels = Object.fromEntries(
    Object.entries(TOP_LEVEL_LABELS).filter(([k]) => !SKIP_TOP_LEVEL.has(k))
  );

  const numberPaths = new Set(
    Object.entries(FIELD_KIND)
      .filter(([, kind]) => kind === "number")
      .map(([path]) => path)
  );

  const handleSubmit = async () => {
    // Only send fields the operator actually filled in — an empty text
    // input is "not provided", not "clear this field to empty string".
    // Booleans and numbers are coerced to their real JSON type here: the
    // backend stores whatever value it's given as-is (no server-side
    // coercion for manual corrections, unlike LLM-extracted fields), so a
    // numeric field left as a string would silently persist as text.
    const fields = Object.fromEntries(
      Object.entries(values)
        .filter(([, v]) => v !== "")
        .map(([path, v]) => {
          if (v === "true") return [path, true];
          if (v === "false") return [path, false];
          if (numberPaths.has(path)) {
            const parsed = Number(v);
            return [path, Number.isNaN(parsed) ? v : parsed];
          }
          return [path, v];
        })
    );

    if (Object.keys(fields).length === 0) {
      toast.error("Renseignez au moins un champ avant d'enregistrer.");
      return;
    }

    setSubmitting(true);
    try {
      await apiClient.post<ClaimOpeningForm>(
        `/claims/${claimId}/documents/opening-form/manual`,
        { fields }
      );
      toast.success(`${Object.keys(fields).length} champ(s) enregistré(s) manuellement`);
      onSubmitted();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.data?.detail || "Échec de l'enregistrement." : "Serveur injoignable.";
      toast.error(typeof message === "string" ? message : "Échec de l'enregistrement.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Saisissez directement les informations connues du sinistre — utile quand le dossier est
        ouvert avant réception des pièces (déclaration téléphonique, par exemple). Les documents
        pourront être ajoutés plus tard ; une correction manuelle n&apos;est jamais écrasée par une
        extraction automatique ultérieure sur le même champ.
      </p>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Police, souscripteur &amp; sinistre</CardTitle>
        </CardHeader>
        <CardContent>
          <SectionInputs
            prefix=""
            labels={topLevelLabels}
            kinds={FIELD_KIND}
            values={values}
            onChange={setField}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Conducteur</CardTitle>
        </CardHeader>
        <CardContent>
          <SectionInputs
            prefix="conducteur"
            labels={CONDUCTEUR_LABELS}
            kinds={CONDUCTEUR_FIELD_KIND}
            values={values}
            onChange={setField}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Partie adverse</CardTitle>
        </CardHeader>
        <CardContent>
          <SectionInputs
            prefix="partie_adverse"
            labels={PARTIE_ADVERSE_LABELS}
            kinds={{}}
            values={values}
            onChange={setField}
          />
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Les victimes ne sont pas encore saisissables ici — ajoutez-les via un document (constat)
        une fois disponible.
      </p>

      <div className="flex justify-end">
        <Button onClick={handleSubmit} disabled={submitting}>
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Enregistrement...
            </>
          ) : (
            "Enregistrer la saisie manuelle"
          )}
        </Button>
      </div>
    </div>
  );
}
