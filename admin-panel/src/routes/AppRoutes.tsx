import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { LoginPage } from '@/pages/auth/LoginPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { BoxesPage } from '@/pages/boxes/BoxesPage';
import { BoxDetailPage } from '@/pages/boxes/BoxDetailPage';
import { CasesPage } from '@/pages/cases/CasesPage';
import { CaseDetailPage } from '@/pages/cases/CaseDetailPage';
import { ItemsPage } from '@/pages/items/ItemsPage';
import { ItemDetailPage } from '@/pages/items/ItemDetailPage';
import { UsersPage } from '@/pages/users/UsersPage';
import { UserDetailPage } from '@/pages/users/UserDetailPage';
import { AuditLogsPage } from '@/pages/audit/AuditLogsPage';
import { ReportsPage } from '@/pages/reports/ReportsPage';
import { MetricsPage } from '@/pages/metrics/MetricsPage';
import { HealthPage } from '@/pages/health/HealthPage';
import { MainLayout } from '@/components/layout/MainLayout';
import { ProtectedRoute } from '@/routes/ProtectedRoute';

const router = createBrowserRouter(
  [
    {
      path: '/login',
      element: <LoginPage />
    },
    {
      element: <ProtectedRoute />,
      children: [
        {
          element: <MainLayout />,
          children: [
            {
              index: true,
              element: <DashboardPage />
            },
            {
              path: 'boxes',
              children: [
                {
                  index: true,
                  element: <BoxesPage />
                },
                {
                  path: ':boxId',
                  element: <BoxDetailPage />
                }
              ]
            },
            {
              path: 'cases',
              children: [
                {
                  index: true,
                  element: <CasesPage />
                },
                {
                  path: ':caseId',
                  element: <CaseDetailPage />
                }
              ]
            },
            {
              path: 'items',
              children: [
                {
                  index: true,
                  element: <ItemsPage />
                },
                {
                  path: ':itemId',
                  element: <ItemDetailPage />
                }
              ]
            },
            {
              path: 'users',
              element: <ProtectedRoute roles={['admin']} />,
              children: [
                {
                  index: true,
                  element: <UsersPage />
                },
                {
                  path: ':userId',
                  element: <UserDetailPage />
                }
              ]
            },
            {
              path: 'audit',
              element: <ProtectedRoute roles={['admin', 'auditor']} />,
              children: [
                {
                  index: true,
                  element: <AuditLogsPage />
                }
              ]
            },
            {
              path: 'reports',
              element: <ProtectedRoute roles={['admin', 'manager']} />,
              children: [
                {
                  index: true,
                  element: <ReportsPage />
                }
              ]
            },
            {
              path: 'metrics',
              element: <ProtectedRoute roles={['admin', 'auditor']} />,
              children: [
                {
                  index: true,
                  element: <MetricsPage />
                }
              ]
            },
            {
              path: 'health',
              element: <ProtectedRoute roles={['admin']} />,
              children: [
                {
                  index: true,
                  element: <HealthPage />
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  { basename: '/admin-panel' }
);

export function AppRoutes() {
  return <RouterProvider router={router} />;
}
