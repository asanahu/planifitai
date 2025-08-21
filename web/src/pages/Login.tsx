import { LoginForm } from '../features/auth/LoginForm';

export default function LoginPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">Login</h1>
      <LoginForm />
    </div>
  );
}
