import { Component, ReactNode } from "react"
import { Button } from "../ui/button"

type ErrorBoundaryProps = {
  children: ReactNode
  fallback?: (error: Error, reset: () => void) => ReactNode
}

type ErrorBoundaryState = {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false,
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  reset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  componentDidCatch(error: Error, errorInfo: unknown) {
    console.error("Admin panel error boundary", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error ?? new Error("Unknown error"), this.reset)
      }
      return (
        <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4">
          <h2 className="text-xl font-semibold">Something went wrong.</h2>
          <pre className="max-w-xl overflow-auto rounded bg-muted p-4 text-sm text-muted-foreground">
            {this.state.error?.message}
          </pre>
          <Button onClick={this.reset}>Try again</Button>
        </div>
      )
    }

    return this.props.children
  }
}
