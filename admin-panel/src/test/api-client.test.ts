import axios from "axios"
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"

import { api } from "../lib/api-client"
import { apiBase } from "../lib/utils"
import { authStore } from "../stores/auth-store"

describe("api client", () => {
  beforeEach(() => {
    authStore.setState({ accessToken: null, refreshToken: null })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("refreshes the access token and retries the original request on 401", async () => {
    authStore.setState({ accessToken: "expired", refreshToken: "refresh-token" })

    const responseHandlers = (api.interceptors.response as unknown as { handlers: Array<{ rejected?: (error: unknown) => any }> })
      .handlers
    const rejectedHandler = responseHandlers.find((handler) => typeof handler.rejected === "function")?.rejected
    if (!rejectedHandler) {
      throw new Error("Response interceptor not registered")
    }

    const refreshMock = vi
      .spyOn(axios, "post")
      .mockResolvedValueOnce({ data: { access_token: "fresh", refresh_token: "new-refresh" } })

    const adapter = vi.fn().mockResolvedValue({
      data: { ok: true },
      status: 200,
      statusText: "OK",
      headers: {},
      config: {},
    })

    const result = await rejectedHandler({
      response: { status: 401 },
      config: { headers: {}, url: "/secure", adapter },
    })

    expect(result.status).toBe(200)
    expect(result.statusText).toBe("OK")
    expect(result.data).toEqual({ ok: true })
    expect(refreshMock).toHaveBeenCalledWith(`${apiBase}/auth/refresh`, { refresh_token: "refresh-token" })
    expect(adapter).toHaveBeenCalledTimes(1)
    expect(authStore.getState().accessToken).toBe("fresh")
    expect(authStore.getState().refreshToken).toBe("new-refresh")
  })
})
