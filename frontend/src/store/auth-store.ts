import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  userId: string | null;
  setAuth: (tokens: { accessToken: string; refreshToken: string; userId?: string | null }) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      userId: null,
      setAuth: ({ accessToken, refreshToken, userId }) =>
        set({ accessToken, refreshToken, userId: userId ?? null }),
      clearAuth: () => set({ accessToken: null, refreshToken: null, userId: null }),
    }),
    { name: "claimos-auth" }
  )
);
