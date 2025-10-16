import axios, { type AxiosRequestConfig } from "axios"
import { apiBase } from "./utils"
import { authStore } from "../stores/auth-store"

declare module "axios" {
  interface AxiosRequestConfig {
    _retry?: boolean
  }
}

export const api = axios.create({
  baseURL: apiBase,
  withCredentials: true,
})

let isRefreshing = false
let refreshQueue: Array<() => void> = []

const processQueue = () => {
  refreshQueue.forEach((cb) => cb())
  refreshQueue = []
}

type RefreshResponse = {
  access_token: string
  refresh_token?: string
}

api.interceptors.request.use((config) => {
  const { accessToken } = authStore.getState()
  if (accessToken && config.headers) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest: AxiosRequestConfig & { _retry?: boolean } = error.config ?? {}
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        await new Promise<void>((resolve) => refreshQueue.push(resolve))
        return api(originalRequest)
      }

      originalRequest._retry = true
      isRefreshing = true
      try {
        const { refreshToken } = authStore.getState()
        if (!refreshToken) {
          authStore.getState().logout()
          return Promise.reject(error)
        }
        const { data } = await axios.post<RefreshResponse>(`${apiBase}/auth/refresh`, { refresh_token: refreshToken })
        authStore.getState().setTokens({
          accessToken: data.access_token,
          refreshToken: data.refresh_token ?? refreshToken,
        })
        processQueue()
        return api(originalRequest)
      } catch (refreshError) {
        authStore.getState().logout()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)
