import { z } from "zod"
import { useTranslation } from "react-i18next"
import { Form } from "../components/forms/form"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../lib/api-client"

const profileSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
})

type ProfileValues = z.infer<typeof profileSchema>

export const SettingsRoute = () => {
  const { t } = useTranslation()

  const saveProfile = async (values: ProfileValues) => {
    await api.put("/profile", values)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{t("navigation.settings")}</h1>
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Update your personal details</CardDescription>
        </CardHeader>
        <CardContent>
          <Form<ProfileValues>
            schema={profileSchema}
            defaultValues={{ name: "", email: "" }}
            onSubmit={saveProfile}
          >
            {(form) => (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" {...form.register("name")} />
                  {form.formState.errors.name && (
                    <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" {...form.register("email")} />
                  {form.formState.errors.email && (
                    <p className="text-sm text-destructive">{form.formState.errors.email.message}</p>
                  )}
                </div>
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting ? "Saving..." : t("actions.save")}
                </Button>
              </div>
            )}
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
