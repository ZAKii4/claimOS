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
                        {claim.status_code === "APPROVED" && <Badge className="bg-green-500/10 text-green-500 hover:bg-green-500/20" variant="secondary">Approved</Badge>}
                        {claim.status_code === "PENDING_REVIEW" && <Badge className="bg-amber-500/10 text-amber-500 hover:bg-amber-500/20" variant="secondary">Review Required</Badge>}
                        {claim.status_code === "FRAUD_ALERT" && <Badge className="bg-red-500/10 text-red-500 hover:bg-red-500/20" variant="secondary">Fraud Alert</Badge>}
                        {claim.status_code === "PROCESSING" && <Badge className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20" variant="secondary">Processing (AI)</Badge>}
                        {claim.status_code === "REJECTED" && <Badge className="bg-red-500/10 text-red-500 hover:bg-red-500/20" variant="secondary">Rejected</Badge>}
                        {!claim.status_code && <Badge variant="outline">{claim.status_code || "Unknown"}</Badge>}
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
