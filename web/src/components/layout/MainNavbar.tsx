import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useQuery } from '@tanstack/react-query';
import { listNotifications } from '../../api/notifications';
import { today } from '../../utils/date';
import { useEffect, useState } from 'react';
import Button from '../ui/button';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
}

export default function MainNavbar() {
  const { user, logout } = useAuth();
  const [installEvt, setInstallEvt] = useState<BeforeInstallPromptEvent | null>(null);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setInstallEvt(e as BeforeInstallPromptEvent);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const onInstall = async () => {
    await installEvt?.prompt();
    setInstallEvt(null);
  };

  const todayStr = today();
  const { data } = useQuery({
    queryKey: ['notifications', todayStr],
    queryFn: () => listNotifications({ date: todayStr, state: 'scheduled|sent_today' }),
    enabled: !!user,
  });
  const count = data?.length ?? 0;

  return (
    <nav role="navigation" aria-label="Main" className="border-b bg-white dark:bg-gray-900">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-xl font-bold bg-gradient-to-r from-planifit-500 to-violet-500 bg-clip-text text-transparent">
          PlanifitAI
        </Link>
        <div className="flex items-center space-x-4 text-sm">
          {user ? (
            <>
              <NavLink to="/today" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Hoy
              </NavLink>
              <NavLink to="/workout" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Workout
              </NavLink>
              <NavLink to="/nutrition/today" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Nutrición
              </NavLink>
              <NavLink to="/shopping-list" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Compras
              </NavLink>
              <NavLink to="/progress" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Progreso
              </NavLink>
              <NavLink to="/reports" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Reportes
              </NavLink>
              <div className="relative">
                <NavLink to="/notifications" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                  Notificaciones
                </NavLink>
                {count > 0 && (
                  <span className="absolute -right-2 -top-2 rounded-full bg-red-500 px-2 text-xs" aria-label="nuevas notificaciones">
                    {count}
                  </span>
                )}
              </div>
              {installEvt && (
                <Button onClick={onInstall} aria-label="Instalar aplicación" variant="ghost">
                  Instalar
                </Button>
              )}
              <Button onClick={logout} variant="ghost">
                Logout
              </Button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Login
              </NavLink>
              <NavLink to="/register" className="px-2 py-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-planifit-500">
                Registro
              </NavLink>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
