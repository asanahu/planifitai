import type { ReactElement } from "react";
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import DashboardPage from './pages/Dashboard';
import TodayPage from './pages/Today';
import ProfileOnboardingPage from './pages/ProfileOnboarding';
import WorkoutPage from './pages/Workout';
import WorkoutGeneratePage from './pages/WorkoutGenerate';
import NutritionTodayPage from './pages/NutritionToday';
import NutritionPlanPage from './pages/NutritionPlan';
import ShoppingListPage from './pages/ShoppingList';
import ProgressPage from './pages/Progress';
import ReportsPage from './pages/Reports';
import { Notifications } from './features/notifications/Notifications';
import Navbar from './components/Navbar';
import { useAuthStore } from './features/auth/useAuthStore';

function PrivateRoute({ children }: { children: ReactElement }) {
  const { accessToken } = useAuthStore();
  return accessToken ? (
    <>
      <Navbar />
      {children}
    </>
  ) : (
    <Navigate to="/login" />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/profile" element={<PrivateRoute><ProfileOnboardingPage /></PrivateRoute>} />
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
    </BrowserRouter>
  );
}
