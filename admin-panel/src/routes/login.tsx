import { z } from "zod"
import { Form } from "../components/forms/form"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { authStore } from "../stores/auth-store"
import { api } from "../lib/api-client"
import { useNavigate } from "react-router-dom"
import { useTranslation } from "react-i18next"

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
})

type LoginValues = z.infer<typeof loginSchema>

export const LoginRoute = () => {
  const navigate = useNavigate()
  const { setTokens, fetchMe } = authStore((state) => ({ setTokens: state.setTokens, fetchMe: state.fetchMe }))
  const { t } = useTranslation()

  const handleSubmit = async (values: LoginValues) => {
    const { data } = await api.post<{ access_token: string; refresh_token: string }>("/auth/login", values)
    setTokens({ accessToken: data.access_token, refreshToken: data.refresh_token })
    await fetchMe()
    navigate("/dashboard")
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{t("navigation.login")}</CardTitle>
          <CardDescription>Access administrative tooling</CardDescription>
        </CardHeader>
        <CardContent>
          <Form<LoginValues> schema={loginSchema} defaultValues={{ email: "", password: "" }} onSubmit={handleSubmit}>
            {(form) => (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" {...form.register("email")} />
                  {form.formState.errors.email && (
                    <p className="text-sm text-destructive">{form.formState.errors.email.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input id="password" type="password" {...form.register("password")} />
                  {form.formState.errors.password && (
                    <p className="text-sm text-destructive">{form.formState.errors.password.message}</p>
                  )}
                </div>
                <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting ? "Signing in..." : "Sign In"}
                </Button>
              </div>
            )}
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
