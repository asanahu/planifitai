import { Link } from 'react-router-dom';
import { LoginForm } from '../features/auth/LoginForm';
import AuthLayout from '../components/layout/AuthLayout';

export default function LoginPage() {
  return (
    <AuthLayout title="Inicia sesión" subtitle="Accede a tu plan inteligente" cardTitle="Bienvenido de nuevo">
      <LoginForm />
      <p className="mt-4 text-center text-sm text-gray-600 dark:text-gray-300">
        ¿No tienes cuenta?{' '}
        <Link to="/register" className="text-planifit-600 hover:underline">
          Regístrate
        </Link>
      </p>
    </AuthLayout>
  );
}
