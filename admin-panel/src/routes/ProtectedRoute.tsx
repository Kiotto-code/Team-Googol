import { useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';
import type { Role } from '@/types/auth';

interface ProtectedRouteProps {
  roles?: Role[];
}

export function ProtectedRoute({ roles }: ProtectedRouteProps) {
  const location = useLocation();
  const { user, accessToken, fetchCurrentUser } = useAuthStore((state) => ({
    user: state.user,
    accessToken: state.accessToken,
    fetchCurrentUser: state.fetchCurrentUser
  }));
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const ensureUser = async () => {
      if (!accessToken) {
        setIsChecking(false);
        return;
      }
      if (!user) {
        await fetchCurrentUser();
      }
      if (isMounted) {
        setIsChecking(false);
      }
    };
    ensureUser();
    return () => {
      isMounted = false;
    };
  }, [accessToken, fetchCurrentUser, user]);

  if (!accessToken && !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span>Loading...</span>
      </div>
    );
  }

  if (roles && user && !roles.some((role) => user.roles.includes(role))) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="rounded-lg border bg-card p-6 text-card-foreground shadow">
          <h2 className="text-lg font-semibold">Access restricted</h2>
          <p className="text-sm text-muted-foreground">You do not have permission to view this content.</p>
        </div>
      </div>
    );
  }

  return <Outlet />;
}
