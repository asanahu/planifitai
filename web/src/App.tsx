import type { ReactElement } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import DashboardPage from './pages/Dashboard';
import TodayPage from './pages/Today';
import OnboardingWizard from './features/onboarding/OnboardingWizard';
import WorkoutPage from './pages/Workout';
import WorkoutGeneratePage from './pages/WorkoutGenerate';
import NutritionTodayPage from './pages/NutritionToday';
import NutritionPlanPage from './pages/NutritionPlan';
import ShoppingListPage from './pages/ShoppingList';
const ProgressPage = lazy(() => import('./pages/Progress'));
const ReportsPage = lazy(() => import('./pages/Reports'));
import { Notifications } from './features/notifications/Notifications';
import Navbar from './components/Navbar';
import { useAuthStore } from './features/auth/useAuthStore';
import { useQuery } from '@tanstack/react-query';
import { getProfile } from './api/profile';
import { getUserRoutines } from './api/routines';

function PrivateRoute({ children }: { children: ReactElement }) {
  const { accessToken } = useAuthStore();
  const location = useLocation();
  const skip = new URLSearchParams(location.search).get('skip') === '1';
  const profileQuery = useQuery({ queryKey: ['profile'], queryFn: getProfile, enabled: !!accessToken });
  const routinesQuery = useQuery({ queryKey: ['routines'], queryFn: getUserRoutines, enabled: !!accessToken });
  if (!accessToken) return <Navigate to="/login" />;
  const needsOnboarding =
    location.pathname !== '/onboarding' &&
    !skip &&
    (profileQuery.data === null || (routinesQuery.data?.length || 0) === 0);
  if (needsOnboarding) return <Navigate to="/onboarding" replace />;
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/onboarding" element={<PrivateRoute><OnboardingWizard /></PrivateRoute>} />
          <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
          <Route path="/today" element={<PrivateRoute><TodayPage /></PrivateRoute>} />
          <Route path="/workout" element={<PrivateRoute><WorkoutPage /></PrivateRoute>} />
          <Route path="/workout/generate" element={<PrivateRoute><WorkoutGeneratePage /></PrivateRoute>} />
          <Route path="/nutrition/today" element={<PrivateRoute><NutritionTodayPage /></PrivateRoute>} />
          <Route path="/nutrition/plan" element={<PrivateRoute><NutritionPlanPage /></PrivateRoute>} />
          <Route path="/shopping-list" element={<PrivateRoute><ShoppingListPage /></PrivateRoute>} />
          <Route path="/progress" element={<PrivateRoute><ProgressPage /></PrivateRoute>} />
          <Route path="/reports" element={<PrivateRoute><ReportsPage /></PrivateRoute>} />
          <Route path="/notifications" element={<PrivateRoute><Notifications /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/today" />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
