"use client";

import React, { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient, ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth-store";

interface MfaSuccessResponse {
  status: "mfa_success";
  access_token: string;
  refresh_token: string;
  token_type: string;
}

function MFAForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = searchParams.get("user_id");
  const setAuth = useAuthStore((s) => s.setAuth);

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!userId) {
      setError("Missing user context — please sign in again.");
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.post<MfaSuccessResponse>("/auth/mfa/verify", {
        user_id: userId,
        code,
      });
      setAuth({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        userId,
      });
      router.push("/");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.data?.detail || "Invalid MFA code");
      } else {
        setError("Unable to reach the server. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-white p-10 shadow-lg">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Two-Factor Authentication
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Open your authenticator app and enter the 6-digit code.
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm">
            <input
              type="text"
              required
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="relative block w-full appearance-none rounded-md border border-gray-300 px-3 py-4 text-center text-2xl tracking-widest text-gray-900 placeholder-gray-300 focus:z-10 focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              placeholder="000000"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative flex w-full justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Verifying..." : "Verify"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function MFAPage() {
  return (
    <Suspense fallback={null}>
      <MFAForm />
    </Suspense>
  );
}
