import { create } from "zustand";

import { api } from "../lib/api";
import type { User } from "../types/api";

type AuthState = {
  user: User | null;
  loading: boolean;
  setUser: (user: User | null) => void;
  restore: () => Promise<void>;
  signOut: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  loading: true,
  setUser: (user) => set({ user, loading: false }),
  restore: async () => {
    try {
      set({ user: await api.me(), loading: false });
    } catch {
      set({ user: null, loading: false });
    }
  },
  signOut: async () => {
    try {
      await api.logout();
    } finally {
      set({ user: null, loading: false });
    }
  },
}));
