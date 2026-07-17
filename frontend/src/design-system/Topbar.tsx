"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, LogOut, Search, UserCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";

interface CurrentOperator {
  full_name: string;
  role: string | null;
}

export function Topbar() {
  const router = useRouter();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const [me, setMe] = useState<CurrentOperator | null>(null);

  useEffect(() => {
    apiClient
      .get<CurrentOperator>("/auth/me")
      .then(setMe)
      .catch((err) => console.error("Failed to load current operator", err));
  }, []);

  const handleLogout = () => {
    clearAuth();
    router.replace("/login");
  };

  return (
    <header className="h-16 border-b bg-card flex items-center justify-between px-6 shadow-sm">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-96">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search claims, agents, workflows (Cmd+K)"
            className="pl-9 bg-muted/50 border-transparent focus-visible:border-primary"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-5 h-5 text-muted-foreground" />
        </Button>
        <div className="flex items-center gap-2 pl-4 border-l">
          <div className="text-right">
            <p className="text-sm font-medium leading-none">{me?.full_name || "..."}</p>
            <p className="text-xs text-muted-foreground">{me?.role || ""}</p>
          </div>
          <Button variant="ghost" size="icon" className="rounded-full">
            <UserCircle className="w-8 h-8" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleLogout} title="Log out">
            <LogOut className="w-4 h-4 text-muted-foreground" />
          </Button>
        </div>
      </div>
    </header>
  );
}
