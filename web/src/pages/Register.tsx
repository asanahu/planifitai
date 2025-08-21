import { RegisterForm } from '../features/auth/RegisterForm';

export default function RegisterPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">Register</h1>
      <RegisterForm />
    </div>
  );
}
