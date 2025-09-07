import { Link } from 'react-router-dom';
import { RegisterForm } from '../features/auth/RegisterForm';
import AuthLayout from '../components/layout/AuthLayout';

export default function RegisterPage() {
  return (
    <AuthLayout title="Crea tu cuenta" subtitle="Empieza con tu plan inteligente" cardTitle="Registro">
      <RegisterForm />
      <p className="mt-4 text-center text-sm text-gray-600 dark:text-gray-300">
        ¿Ya tienes cuenta?{' '}
        <Link to="/login" className="text-planifit-600 hover:underline">
          Inicia sesión
        </Link>
      </p>
    </AuthLayout>
  );
}
