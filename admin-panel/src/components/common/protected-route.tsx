import { ReactNode, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { authStore, hasAnyRole, Role } from "../../stores/auth-store"

export const ProtectedRoute = ({ roles, children }: { roles?: Role[]; children: ReactNode }) => {
  const navigate = useNavigate()
  const { user, loading, fetchMe } = authStore((state) => ({
    user: state.user,
    loading: state.loading,
    fetchMe: state.fetchMe,
  }))

  useEffect(() => {
    if (!user && !loading) {
      void fetchMe()
    }
  }, [user, loading, fetchMe])

  useEffect(() => {
    if (!loading && !user) {
      navigate("/login")
    }
    if (!loading && user && !hasAnyRole(roles, user)) {
      navigate("/unauthorized", { replace: true })
    }
  }, [user, loading, navigate, roles])

  if (!user) {
    return <div className="flex min-h-[50vh] items-center justify-center">Loading...</div>
  }

  return <>{children}</>
}
