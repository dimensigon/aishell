import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { useAuthStore } from '@store/authStore';
import { useThemeStore } from '@store/themeStore';
import websocket from '@services/websocket';

// Pages
import { LoginForm } from '@components/auth/LoginForm';
import { RegisterForm } from '@components/auth/RegisterForm';
import { DashboardLayout } from '@components/common/DashboardLayout';
import { ConnectionManager } from '@components/database/ConnectionManager';
import { QueryEditor } from '@components/query/QueryEditor';
import { VisualQueryBuilder } from '@components/query/VisualQueryBuilder';
import { PerformanceDashboard } from '@components/dashboard/PerformanceDashboard';
import { UserManagement } from '@components/admin/UserManagement';
import { AuditLogViewer } from '@components/admin/AuditLogViewer';
import { SettingsPage } from '@pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

const App: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const { mode } = useThemeStore();

  const theme = createTheme({
    palette: {
      mode,
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      websocket.connect();
    }

    return () => {
      websocket.disconnect();
    };
  }, [isAuthenticated]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />

            <Route
              path="/*"
              element={
                isAuthenticated ? (
                  <DashboardLayout>
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" />} />
                      <Route path="/dashboard" element={<PerformanceDashboard />} />
                      <Route path="/connections" element={<ConnectionManager />} />
                      <Route path="/query" element={<QueryEditor />} />
                      <Route path="/visual-query" element={<VisualQueryBuilder />} />
                      <Route path="/users" element={<UserManagement />} />
                      <Route path="/audit" element={<AuditLogViewer />} />
                      <Route path="/settings" element={<SettingsPage />} />
                    </Routes>
                  </DashboardLayout>
                ) : (
                  <Navigate to="/login" />
                )
              }
            />
          </Routes>
        </BrowserRouter>

        <ToastContainer
          position="bottom-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default App;
