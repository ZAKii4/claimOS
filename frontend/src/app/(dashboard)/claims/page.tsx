"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, FileText, CheckCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/lib/api-client";
import { NewClaimWizard } from "@/components/claims/NewClaimWizard";

interface ClaimSummary {
  id: string;
  external_ref: string;
  date_of_loss: string;
  date_received: string;
  stp_eligible: boolean;
  composite_confidence: string;
  claim_type_code: string;
  status_code: string;
}

interface ClaimType {
  id: string;
  code: string;
  label_fr: string;
}

// Mirrors the real backend enum (app/config/constants.py::ClaimStatusCode) —
// every value a claim can actually have, not a fictional/mocked subset.
// Previously only 5 statuses were handled here (APPROVED, PENDING_REVIEW,
// FRAUD_ALERT, PROCESSING, REJECTED) — none of which exist in the real
// enum except REJECTED, so the status badge was blank for every real claim
// (including INGESTED, the status every new claim starts with).
const STATUS_BADGE: Record<string, { label: string; className: string }> = {
  INGESTED: { label: "Ingested", className: "bg-secondary text-secondary-foreground" },
  PREPROCESSING: { label: "Preprocessing", className: "bg-blue-500/10 text-blue-500" },
  OCR_IN_PROGRESS: { label: "OCR In Progress", className: "bg-blue-500/10 text-blue-500" },
  CLASSIFYING: { label: "Classifying", className: "bg-blue-500/10 text-blue-500" },
  EXTRACTING: { label: "Extracting", className: "bg-blue-500/10 text-blue-500" },
  VALIDATING: { label: "Validating", className: "bg-blue-500/10 text-blue-500" },
  AWAITING_REVIEW: { label: "Review Required", className: "bg-amber-500/10 text-amber-500" },
  PENDING_DOCUMENTS: { label: "Pending Documents", className: "bg-amber-500/10 text-amber-500" },
  VALIDATED: { label: "Validated", className: "bg-green-500/10 text-green-500" },
  REJECTED: { label: "Rejected", className: "bg-red-500/10 text-red-500" },
  ARCHIVED: { label: "Archived", className: "bg-secondary text-secondary-foreground" },
};

export default function ClaimsWorkspacePage() {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const [claimTypes, setClaimTypes] = useState<ClaimType[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchClaims = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<{ items: ClaimSummary[] }>("/claims");
      setClaims(data.items);
    } catch (error) {
      toast.error("Erreur de chargement des sinistres");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClaims();
  }, []);

  const openDialog = async () => {
    setDialogOpen(true);
    if (claimTypes.length === 0) {
      try {
        const types = await apiClient.get<ClaimType[]>("/lookups/claim-types");
        setClaimTypes(types);
      } catch (err) {
        console.error("Failed to load claim types", err);
      }
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Claims Workspace</h1>
        <Button onClick={openDialog}>
          <FileText className="mr-2 h-4 w-4" /> New Claim
        </Button>
      </div>

      <NewClaimWizard
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        claimTypes={claimTypes}
        onClaimCreated={fetchClaims}
      />

      <Card className="flex-1">
        <CardHeader>
          <CardTitle>Recent Claims</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Claim Ref</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Date of Loss</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>AI Confidence</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {claims.map((claim) => {
                  const conf = parseFloat(claim.composite_confidence || "0");
                  return (
                    <TableRow key={claim.id}>
                      <TableCell className="font-medium">{claim.external_ref}</TableCell>
                      <TableCell>{claim.claim_type_code}</TableCell>
                      <TableCell>{claim.date_of_loss}</TableCell>
                      <TableCell>
                        {(() => {
                          const status = STATUS_BADGE[claim.status_code];
                          return status ? (
                            <Badge className={status.className} variant="secondary">
                              {status.label}
                            </Badge>
                          ) : (
                            <Badge variant="outline">{claim.status_code || "Unknown"}</Badge>
                          );
                        })()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 rounded-full bg-secondary overflow-hidden">
                            <div
                              className={`h-full ${conf > 0.9 ? 'bg-green-500' : conf > 0.7 ? 'bg-amber-500' : 'bg-red-500'}`}
                              style={{ width: `${conf * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-muted-foreground">{(conf * 100).toFixed(0)}%</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/claims/${claim.id}`}>
                          <Button variant="ghost" size="icon">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                        <Button variant="ghost" size="icon" className="text-green-500">
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
