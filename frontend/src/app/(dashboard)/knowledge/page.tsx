"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Database, Share2, Bot } from "lucide-react";
import { apiClient, ApiError } from "@/lib/api-client";

interface HybridSearchResponse {
  status: string;
  response: string;
  context_used: {
    query: string;
    vector_sources: number;
    graph_sources: number;
  };
}

export default function KnowledgeBasePage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<HybridSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    setError(null);
    try {
      const data = await apiClient.post<HybridSearchResponse>("/knowledge/hybrid-search", {
        tenant_id: "default",
        query: query.trim(),
      });
      setResult(data);
    } catch (err) {
      console.error("Search failed", err);
      setResult(null);
      setError(
        err instanceof ApiError
          ? err.data?.detail || "Search failed."
          : "Unable to reach the server."
      );
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Enterprise Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">Hybrid search across vector embeddings and the knowledge graph, answered by a real local LLM.</p>
        </div>
        <div className="flex gap-2">
          <span className="inline-flex items-center rounded-md bg-secondary px-2 py-1 text-xs font-medium text-secondary-foreground">
            <Share2 className="w-3 h-3 mr-1" /> Connected to RAG
          </span>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question about ingested claims, documents, or policies..."
                className="pl-10 h-12 text-lg"
              />
            </div>
            <Button type="submit" size="lg" disabled={isSearching || !query.trim()} className="h-12 px-8">
              {isSearching ? "Searching..." : "Search"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {!hasSearched ? (
        <Card className="border-dashed border-2 bg-transparent text-center p-12">
          <CardContent className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-muted rounded-full">
              <Database className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-medium tracking-tight">AI-Powered Enterprise Search</h3>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Our hybrid search engine combines semantic vector similarity with the knowledge graph, then asks a real LLM to answer grounded in what it finds. Enter a query above.
            </p>
          </CardContent>
        </Card>
      ) : error ? (
        <div className="p-8 text-center text-sm text-red-600 border rounded-lg bg-red-50 dark:bg-red-950" role="alert">
          {error}
        </div>
      ) : (
        <div className="space-y-4">
          {isSearching ? (
            <div className="p-8 text-center text-muted-foreground">Searching and generating an answer...</div>
          ) : result ? (
            <Card>
              <CardHeader className="flex flex-row items-center gap-3 space-y-0">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Bot className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-base font-medium">AI Answer</CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    Grounded in {result.context_used.vector_sources} document source(s) and{" "}
                    {result.context_used.graph_sources} graph node(s)
                    {result.status === "cache_hit" ? " · served from semantic cache" : ""}
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.response}</p>
              </CardContent>
            </Card>
          ) : null}
        </div>
      )}
    </div>
  );
}
