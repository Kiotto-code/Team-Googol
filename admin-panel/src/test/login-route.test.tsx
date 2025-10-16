import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { LoginRoute } from "../routes/login"
import { api } from "../lib/api-client"

const navigateMock = vi.fn()
const setTokensMock = vi.fn()
const fetchMeMock = vi.fn()

vi.mock("../stores/auth-store", () => {
  const authStore = ((selector: (state: { setTokens: typeof setTokensMock; fetchMe: typeof fetchMeMock }) => unknown) =>
    selector({ setTokens: setTokensMock, fetchMe: fetchMeMock })) as any
  authStore.getState = () => ({ setTokens: setTokensMock, fetchMe: fetchMeMock })
  authStore.setState = vi.fn()
  authStore.subscribe = vi.fn()
  return { authStore, hasAnyRole: vi.fn() }
})

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom")
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe("LoginRoute", () => {
  beforeEach(() => {
    navigateMock.mockReset()
    setTokensMock.mockReset()
    fetchMeMock.mockReset()
    fetchMeMock.mockResolvedValue(undefined)
  })

  it("submits credentials, stores tokens, loads the profile, and redirects to the dashboard", async () => {
    const user = userEvent.setup()
    const postMock = vi
      .spyOn(api, "post")
      .mockResolvedValueOnce({ data: { access_token: "token", refresh_token: "refresh" } })

    render(<LoginRoute />)

    await user.type(screen.getByLabelText(/Email/i), "admin@example.com")
    await user.type(screen.getByLabelText(/Password/i), "supersecret")
    await user.click(screen.getByRole("button", { name: /Sign In/i }))

    await waitFor(() => {
      expect(postMock).toHaveBeenCalledWith("/auth/login", {
        email: "admin@example.com",
        password: "supersecret",
      })
      expect(setTokensMock).toHaveBeenCalledWith({ accessToken: "token", refreshToken: "refresh" })
      expect(fetchMeMock).toHaveBeenCalled()
      expect(navigateMock).toHaveBeenCalledWith("/dashboard")
    })
  })
})
