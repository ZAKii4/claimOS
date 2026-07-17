"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

/**
 * Redirects to /login when there is no access token. Every dashboard API
 * call now requires a real Bearer token (see get_current_operator on the
 * backend) — previously a visitor could reach any dashboard page without
 * ever logging in.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);
  const [hasHydrated, setHasHydrated] = useState(false);

  useEffect(() => {
    // Only touch the persist API on the client, after mount — evaluating it
    // during server-side prerendering throws (no localStorage there).
    if (useAuthStore.persist.hasHydrated()) {
      setHasHydrated(true);
      return;
    }
    const unsub = useAuthStore.persist.onFinishHydration(() => setHasHydrated(true));
    return unsub;
  }, []);

  useEffect(() => {
    if (hasHydrated && !accessToken) {
      router.replace("/login");
    }
  }, [hasHydrated, accessToken, router]);

  if (!hasHydrated || !accessToken) {
    return null;
  }

  return <>{children}</>;
}
