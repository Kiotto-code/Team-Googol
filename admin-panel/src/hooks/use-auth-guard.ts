import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { authStore, hasAnyRole, type Role } from "../stores/auth-store"

export function useAuthGuard(requiredRoles?: Role[]) {
  const navigate = useNavigate()
  const { user, loading, fetchMe } = authStore()

  useEffect(() => {
    if (!user && !loading) {
      fetchMe()
    }
  }, [user, loading, fetchMe])

  useEffect(() => {
    if (!loading && requiredRoles && !hasAnyRole(requiredRoles, user)) {
      navigate("/admin-panel/login")
    }
  }, [requiredRoles, user, navigate, loading])

  return { user, loading }
}
