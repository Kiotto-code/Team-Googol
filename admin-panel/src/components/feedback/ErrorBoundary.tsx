import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Trans, withTranslation } from 'react-i18next';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class ErrorBoundaryBase extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    hasError: false
  };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center space-y-4 bg-background p-6 text-center text-foreground">
          <h1 className="text-2xl font-semibold">
            <Trans i18nKey="errors.boundaryTitle">Something went wrong</Trans>
          </h1>
          <p className="max-w-md text-muted-foreground">
            <Trans i18nKey="errors.boundaryMessage">
              Please refresh the page or contact support if the problem persists.
            </Trans>
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}

export const ErrorBoundary = withTranslation()(ErrorBoundaryBase);
