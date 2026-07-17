"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ArrowLeft, Upload, Loader2, FileText } from "lucide-react";
import { toast } from "sonner";
import { apiClient, ApiError } from "@/lib/api-client";
import { ClaimReviewPanel } from "@/components/claims/ClaimReviewPanel";
import { ManualEntryForm } from "@/components/claims/ManualEntryForm";
import { AgentCollaborationPanel } from "@/components/claims/AgentCollaborationPanel";

const DOCUMENT_ROLES = [
  { value: "OWN_VEHICLE", label: "Véhicule assuré" },
  { value: "ADVERSE_VEHICLE", label: "Véhicule adverse" },
  { value: "POLICY_HOLDER", label: "Souscripteur" },
  { value: "VICTIM", label: "Victime" },
  { value: "ACCIDENT_REPORT", label: "Constat / PV" },
];

interface ClaimRead {
  id: string;
  external_ref: string;
  date_of_loss: string;
  status_code: string;
  claim_type_code: string;
}

interface IngestedDocument {
  id: string;
  claim_id: string;
  document_type: string;
  document_role: string | null;
  classification_confidence: string | null;
  page_range_start: number;
  page_range_end: number;
  storage_uri: string;
  created_at: string;
  pipeline_warnings: string[];
}

export default function ClaimDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id: claimId } = use(params);

  const [claim, setClaim] = useState<ClaimRead | null>(null);
  const [documents, setDocuments] = useState<IngestedDocument[]>([]);
  const [loadingClaim, setLoadingClaim] = useState(true);
  const [reviewKey, setReviewKey] = useState(0);

  const [file, setFile] = useState<File | null>(null);
  const [role, setRole] = useState("");
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fetchClaim = async () => {
    try {
      const data = await apiClient.get<ClaimRead>(`/claims/${claimId}`);
      setClaim(data);
    } catch {
      toast.error("Impossible de charger ce sinistre");
    } finally {
      setLoadingClaim(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      const data = await apiClient.get<IngestedDocument[]>(`/claims/${claimId}/documents`);
      setDocuments(data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchClaim();
    fetchDocuments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [claimId]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setUploadError("Sélectionnez un fichier.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (role) formData.append("document_role", role);

      const result = await apiClient.postForm<IngestedDocument>(`/claims/${claimId}/documents`, formData);

      if (result.pipeline_warnings.length > 0) {
        toast.warning(`Document traité avec ${result.pipeline_warnings.length} avertissement(s)`);
      } else {
        toast.success("Document traité — pipeline réel exécuté sans erreur");
      }
      setFile(null);
      setRole("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      fetchDocuments();
      setReviewKey((k) => k + 1); // forces ClaimReviewPanel to refetch
    } catch (err) {
      const message =
        err instanceof ApiError ? err.data?.detail || "Échec du traitement du document." : "Serveur injoignable.";
      setUploadError(typeof message === "string" ? message : "Échec du traitement du document.");
    } finally {
      setUploading(false);
    }
  };

  if (loadingClaim) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!claim) {
    return <p className="text-muted-foreground p-6">Sinistre introuvable.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/claims">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{claim.external_ref}</h1>
          <p className="text-sm text-muted-foreground">
            {claim.claim_type_code} · Sinistre du {claim.date_of_loss}
          </p>
        </div>
      </div>

      <Tabs defaultValue="documents">
        <TabsList>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="manual-entry">Saisie manuelle</TabsTrigger>
          <TabsTrigger value="opening-form">Formulaire d&apos;ouverture</TabsTrigger>
          <TabsTrigger value="agents">Analyse IA</TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ajouter un document</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpload} className="flex flex-wrap items-end gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Fichier</label>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm file:mr-3 file:border-0 file:bg-transparent file:text-sm file:font-medium"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Rôle du document</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="flex h-10 w-64 rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="">Non spécifié</option>
                    {DOCUMENT_ROLES.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
                <Button type="submit" disabled={uploading}>
                  {uploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Traitement en cours (OCR + IA, ~1 min)...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" /> Traiter le document
                    </>
                  )}
                </Button>
              </form>
              {uploadError && (
                <p className="text-sm text-red-600 mt-2" role="alert">
                  {uploadError}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Documents traités ({documents.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {documents.length === 0 ? (
                <p className="text-sm text-muted-foreground">Aucun document n&apos;a encore été traité pour ce sinistre.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type détecté</TableHead>
                      <TableHead>Rôle</TableHead>
                      <TableHead>Confiance classification</TableHead>
                      <TableHead>Pages</TableHead>
                      <TableHead>Avertissements</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" /> {doc.document_type}
                        </TableCell>
                        <TableCell>
                          {doc.document_role ? (
                            <Badge variant="outline">{doc.document_role}</Badge>
                          ) : (
                            <span className="text-muted-foreground text-xs">non tagué</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {doc.classification_confidence
                            ? `${Math.round(parseFloat(doc.classification_confidence) * 100)}%`
                            : "—"}
                        </TableCell>
                        <TableCell>
                          {doc.page_range_start}–{doc.page_range_end}
                        </TableCell>
                        <TableCell>
                          {doc.pipeline_warnings.length > 0 ? (
                            <Badge className="bg-amber-500/10 text-amber-500" variant="secondary">
                              {doc.pipeline_warnings.length}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground text-xs">aucun</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manual-entry">
          <ManualEntryForm claimId={claimId} onSubmitted={() => setReviewKey((k) => k + 1)} />
        </TabsContent>

        <TabsContent value="opening-form">
          <ClaimReviewPanel key={reviewKey} claimId={claimId} />
        </TabsContent>

        <TabsContent value="agents">
          <AgentCollaborationPanel claimId={claimId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
