import { useState } from "react"
import { Button } from "../ui/button"
import { Textarea } from "../ui/textarea"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../ui/card"
import { api } from "../../lib/api-client"
import { useTranslation } from "react-i18next"

export const AuditFeedback = () => {
  const { t } = useTranslation()
  const [value, setValue] = useState("")
  const [submitted, setSubmitted] = useState(false)

  const submitFeedback = async () => {
    await api.post("/audit/feedback", { message: value })
    setSubmitted(true)
    setValue("")
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Audit Feedback</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <Textarea value={value} onChange={(event) => setValue(event.target.value)} placeholder="Share audit insights" />
        {submitted && <p className="text-sm text-muted-foreground">{t("feedback.auditThanks")}</p>}
      </CardContent>
      <CardFooter>
        <Button size="sm" onClick={submitFeedback} disabled={!value}>
          Submit
        </Button>
      </CardFooter>
    </Card>
  )
}
