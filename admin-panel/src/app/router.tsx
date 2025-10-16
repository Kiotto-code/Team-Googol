import { createBrowserRouter, Navigate } from "react-router-dom"
import { AdminLayout } from "../components/layout/admin-layout"
import { LoginRoute } from "../routes/login"
import { DashboardRoute } from "../routes/dashboard"
import { BoxesRoute } from "../routes/boxes"
import { CasesRoute } from "../routes/cases"
import { ItemsRoute } from "../routes/items"
import { UsersRoute } from "../routes/users"
import { AuditLogsRoute } from "../routes/audit-logs"
import { ReportsRoute } from "../routes/reports"
import { MetricsRoute } from "../routes/metrics"
import { HealthRoute } from "../routes/health"
import { SettingsRoute } from "../routes/settings"
import { UnauthorizedRoute } from "../routes/unauthorized"
import { ProtectedRoute } from "../components/common/protected-route"

export const router = createBrowserRouter(
  [
    {
      path: "/",
      children: [
        { index: true, element: <Navigate to="/dashboard" replace /> },
        { path: "login", element: <LoginRoute /> },
        { path: "unauthorized", element: <UnauthorizedRoute /> },
        {
          element: (
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          ),
          children: [
            { path: "dashboard", element: <DashboardRoute /> },
            {
              path: "boxes",
              element: (
                <ProtectedRoute roles={["admin", "manager", "support"]}>
                  <BoxesRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "cases",
              element: (
                <ProtectedRoute roles={["admin", "manager"]}>
                  <CasesRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "items",
              element: (
                <ProtectedRoute roles={["admin", "manager", "analyst"]}>
                  <ItemsRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "users",
              element: (
                <ProtectedRoute roles={["admin"]}>
                  <UsersRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "audit-logs",
              element: (
                <ProtectedRoute roles={["admin", "auditor"]}>
                  <AuditLogsRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "reports",
              element: (
                <ProtectedRoute roles={["admin", "analyst"]}>
                  <ReportsRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "metrics",
              element: (
                <ProtectedRoute roles={["admin", "analyst"]}>
                  <MetricsRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "health",
              element: (
                <ProtectedRoute roles={["admin", "support"]}>
                  <HealthRoute />
                </ProtectedRoute>
              ),
            },
            {
              path: "settings",
              element: (
                <ProtectedRoute roles={["admin"]}>
                  <SettingsRoute />
                </ProtectedRoute>
              ),
            },
          ],
        },
      ],
    },
  ],
  { basename: "/admin-panel" },
)
