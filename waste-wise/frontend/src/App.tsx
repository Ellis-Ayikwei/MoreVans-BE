import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './store/authStore';
import wsService from './services/websocket';

// Layouts
import DashboardLayout from './components/layouts/DashboardLayout';
import AuthLayout from './components/layouts/AuthLayout';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';

// Dashboard Pages
import Dashboard from './pages/Dashboard';
import BinsMap from './pages/bins/BinsMap';
import BinsList from './pages/bins/BinsList';
import BinDetails from './pages/bins/BinDetails';
import RoutesList from './pages/routes/RoutesList';
import RouteDetails from './pages/routes/RouteDetails';
import RoutePlanning from './pages/routes/RoutePlanning';
import AlertsList from './pages/alerts/AlertsList';
import AlertDetails from './pages/alerts/AlertDetails';
import Analytics from './pages/analytics/Analytics';
import Reports from './pages/analytics/Reports';
import Users from './pages/users/Users';
import Vehicles from './pages/vehicles/Vehicles';
import Settings from './pages/Settings';
import Profile from './pages/Profile';

// Components
import PrivateRoute from './components/PrivateRoute';
import LoadingScreen from './components/LoadingScreen';

function App() {
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    // Connect WebSocket when authenticated
    if (isAuthenticated && user) {
      wsService.connect();
    }

    return () => {
      // Cleanup WebSocket connection
      if (wsService.isConnected()) {
        wsService.disconnect();
      }
    };
  }, [isAuthenticated, user]);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              style: {
                background: '#059669',
              },
            },
            error: {
              style: {
                background: '#DC2626',
              },
            },
          }}
        />

        <Routes>
          {/* Auth Routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
          </Route>

          {/* Protected Dashboard Routes */}
          <Route
            element={
              <PrivateRoute>
                <DashboardLayout />
              </PrivateRoute>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            
            {/* Bins Management */}
            <Route path="/bins">
              <Route index element={<Navigate to="map" replace />} />
              <Route path="map" element={<BinsMap />} />
              <Route path="list" element={<BinsList />} />
              <Route path=":id" element={<BinDetails />} />
            </Route>

            {/* Routes Management */}
            <Route path="/routes">
              <Route index element={<RoutesList />} />
              <Route path="planning" element={<RoutePlanning />} />
              <Route path=":id" element={<RouteDetails />} />
            </Route>

            {/* Alerts */}
            <Route path="/alerts">
              <Route index element={<AlertsList />} />
              <Route path=":id" element={<AlertDetails />} />
            </Route>

            {/* Analytics */}
            <Route path="/analytics">
              <Route index element={<Analytics />} />
              <Route path="reports" element={<Reports />} />
            </Route>

            {/* Fleet Management */}
            <Route path="/vehicles" element={<Vehicles />} />

            {/* User Management (Admin only) */}
            {user?.role === 'admin' && (
              <Route path="/users" element={<Users />} />
            )}

            {/* Settings & Profile */}
            <Route path="/settings" element={<Settings />} />
            <Route path="/profile" element={<Profile />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
