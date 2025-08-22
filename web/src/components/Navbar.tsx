import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listNotifications } from '../api/notifications';
import { today } from '../utils/date';
import { useEffect, useState } from 'react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
}

export default function Navbar() {
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
  });
  const count = data?.length ?? 0;
  return (
    <nav role="navigation" aria-label="Main" className="flex items-center justify-between bg-gray-800 p-4 text-white">
      <div className="font-bold">PlanifitAI</div>
      <ul className="flex space-x-4 text-sm">
        <li>
          <NavLink to="/today" className="px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Hoy</NavLink>
        </li>
        <li>
          <NavLink to="/workout" className="px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Workout</NavLink>
        </li>
        <li className="relative group">
          <span className="cursor-pointer px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded" tabIndex={0}>Nutrition</span>
          <ul className="absolute left-0 mt-2 hidden w-32 space-y-1 rounded bg-gray-800 p-2 group-hover:block">
            <li>
              <NavLink to="/nutrition/today" className="block px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Today</NavLink>
            </li>
            <li>
              <NavLink to="/nutrition/plan" className="block px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Plan</NavLink>
            </li>
          </ul>
        </li>
        <li>
          <NavLink to="/shopping-list" className="px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Shopping List</NavLink>
        </li>
        <li>
          <NavLink to="/progress" className="px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Progress</NavLink>
        </li>
        <li>
          <NavLink to="/reports" className="px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Reports</NavLink>
        </li>
        <li className="relative">
          <NavLink to="/notifications" className="px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded">Notifications</NavLink>
          {count > 0 && (
            <span className="absolute -right-2 -top-2 rounded-full bg-red-500 px-2 text-xs" aria-label="nuevas notificaciones">
              {count}
            </span>
          )}
        </li>
        {installEvt && (
          <li>
            <button
              onClick={onInstall}
              aria-label="Instalar aplicación"
              className="px-2 py-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white rounded"
            >
              Instalar
            </button>
          </li>
        )}
      </ul>
    </nav>
  );
}