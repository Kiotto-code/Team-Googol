import { create } from "zustand"
import { persist } from "zustand/middleware"
import { api } from "../lib/api-client"

export type Role =
  | "admin"
  | "manager"
  | "auditor"
  | "analyst"
  | "support"

export interface AdminUser {
  id: string
  email: string
  name: string
  roles: Role[]
  timezone?: string
}

interface AuthState {
  user: AdminUser | null
  accessToken: string | null
  refreshToken: string | null
  loading: boolean
  error: string | null
  setTokens: (tokens: { accessToken: string; refreshToken: string }) => void
  setUser: (user: AdminUser | null) => void
  fetchMe: () => Promise<AdminUser | null>
  logout: () => void
}

export const authStore = create<AuthState>()(
  persist(
    (set, _get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      loading: false,
      error: null,
      setTokens: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      setUser: (user) => set({ user }),
      fetchMe: async () => {
        set({ loading: true, error: null })
        try {
          const { data } = await api.get<AdminUser & { timezone?: string }>("/auth/me")
          set({ user: data, loading: false })
          return data
        } catch (error) {
          set({ user: null, loading: false, error: "Unable to load profile" })
          return null
        }
      },
      logout: () => {
        set({ user: null, accessToken: null, refreshToken: null })
      },
    }),
    {
      name: "admin-auth",
      partialize: ({ accessToken, refreshToken, user }) => ({ accessToken, refreshToken, user }),
    },
  ),
)

export const hasAnyRole = (roles: Role[] | undefined, user: AdminUser | null) => {
  if (!roles?.length) return true
  if (!user) return false
  return roles.some((role) => user.roles.includes(role))
}
