import type { ReactElement } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import DashboardPage from './pages/Dashboard';
import TodayPage from './pages/Today';
import PerfilPage from './pages/Perfil';
import OnboardingWizard from './features/onboarding/OnboardingWizard';
import WorkoutPage from './pages/Workout';
import WorkoutGeneratePage from './pages/WorkoutGenerate';
import NutritionTodayPage from './pages/NutritionToday';
import NutritionPlanPage from './pages/NutritionPlan';
import ShoppingListPage from './pages/ShoppingList';
import ExerciseCatalogPage from './pages/ExerciseCatalog';
import AdminImportPage from './pages/AdminImport';
const ProgressPage = lazy(() => import('./pages/Progress'));
const ReportsPage = lazy(() => import('./pages/Reports'));
import { Notifications } from './features/notifications/Notifications';
import MainNavbar from './components/layout/MainNavbar';
import LandingPage from './pages/Landing';
import { useAuthStore } from './features/auth/useAuthStore';
import { useQuery } from '@tanstack/react-query';
import { getMe } from './api/users';

function PrivateRoute({ children }: { children: ReactElement }) {
  const { accessToken } = useAuthStore();
  const location = useLocation();
  const meQuery = useQuery({ queryKey: ['me'], queryFn: getMe, enabled: !!accessToken });
  if (!accessToken) return <Navigate to="/login" />;
  const isProfileRoute = location.pathname === '/perfil';
  const incomplete = meQuery.data && meQuery.data.profile_completed === false;
  if (!isProfileRoute && incomplete) return <Navigate to="/perfil" replace />;
  return (
    <>
      <MainNavbar />
      {children}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/onboarding" element={<PrivateRoute><OnboardingWizard /></PrivateRoute>} />
          <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
          <Route path="/today" element={<PrivateRoute><TodayPage /></PrivateRoute>} />
          <Route path="/hoy" element={<PrivateRoute><TodayPage /></PrivateRoute>} />
          <Route path="/perfil" element={<PrivateRoute><PerfilPage /></PrivateRoute>} />
          <Route path="/workout" element={<PrivateRoute><WorkoutPage /></PrivateRoute>} />
          <Route path="/exercises" element={<PrivateRoute><ExerciseCatalogPage /></PrivateRoute>} />
          <Route path="/workout/generate" element={<PrivateRoute><WorkoutGeneratePage /></PrivateRoute>} />
          <Route path="/nutrition/today" element={<PrivateRoute><NutritionTodayPage /></PrivateRoute>} />
          <Route path="/nutrition/plan" element={<PrivateRoute><NutritionPlanPage /></PrivateRoute>} />
          <Route path="/shopping-list" element={<PrivateRoute><ShoppingListPage /></PrivateRoute>} />
          <Route path="/progress" element={<PrivateRoute><ProgressPage /></PrivateRoute>} />
          <Route path="/reports" element={<PrivateRoute><ReportsPage /></PrivateRoute>} />
          <Route path="/notifications" element={<PrivateRoute><Notifications /></PrivateRoute>} />
          <Route path="/admin/import" element={<PrivateRoute><AdminImportPage /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/hoy" />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
