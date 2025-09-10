import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { register as apiRegister, login as apiLogin } from '../../api/auth';
import { useAuthStore } from './useAuthStore';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/ui/button';
import Overlay from '../../components/ui/Overlay';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

type FormData = z.infer<typeof schema>;

export function RegisterForm() {
  const { setTokens, setUser } = useAuthStore();
  const navigate = useNavigate();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    setErrorMsg(null);
    try {
      const user = await apiRegister({ email: data.email, password: data.password });
      const tokens = await apiLogin({ username: data.email, password: data.password });
      setTokens(tokens.access_token, tokens.refresh_token);
      setUser(user);
      navigate('/hoy');
    } catch (e: any) {
      const msg = e?.message || 'No se pudo registrar';
      setErrorMsg(msg);
    }
  };

  const inputClass =
    'w-full rounded-md border border-gray-300 bg-white p-3 text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-planifit-500 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="relative mx-auto max-w-sm space-y-4">
      <div>
        <input
          {...register('email')}
          placeholder="Correo electrónico"
          className={inputClass}
          autoComplete="email"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-500">{errors.email.message}</p>
        )}
      </div>
      <div>
        <input
          {...register('password')}
          type="password"
          placeholder="Contraseña"
          className={inputClass}
          autoComplete="new-password"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-500">{errors.password.message}</p>
        )}
      </div>
      <Button type="submit" className="w-full">
        Crear cuenta
      </Button>
      {errorMsg && (
        <div className="text-center text-sm text-red-600">
          {errorMsg}. ¿Ya tienes cuenta?{' '}
          <a href="/login" className="underline">Inicia sesión</a>
        </div>
      )}
      {isSubmitting && <Overlay>Creando tu cuenta…</Overlay>}
    </form>
  );
}
