import { Suspense } from 'react';
import { AppRoutes } from '@/routes/AppRoutes';
import { Toaster } from 'sonner';
import { ErrorBoundary } from '@/components/feedback/ErrorBoundary';

export default function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
        <AppRoutes />
        <Toaster richColors position="top-right" />
      </Suspense>
    </ErrorBoundary>
  );
}
