import { zodResolver } from "@hookform/resolvers/zod"
import { type ZodTypeAny } from "zod"
import { useForm, type UseFormReturn, type FieldValues, type SubmitHandler } from "react-hook-form"
import { ReactNode } from "react"

interface FormProps<TFieldValues extends FieldValues = FieldValues> {
  schema: ZodTypeAny
  defaultValues: TFieldValues
  onSubmit: SubmitHandler<TFieldValues>
  children: (methods: UseFormReturn<TFieldValues>) => ReactNode
}

export function Form<TFieldValues extends FieldValues = FieldValues>({ schema, defaultValues, onSubmit, children }: FormProps<TFieldValues>) {
  const resolverFactory = zodResolver as unknown as (schema: ZodTypeAny) => unknown
  const methods = useForm<TFieldValues>({
    resolver: resolverFactory(schema) as any,
    defaultValues: defaultValues as any,
    mode: "onBlur",
  })

  return <form onSubmit={methods.handleSubmit(onSubmit as SubmitHandler<TFieldValues>)}>{children(methods)}</form>
}
