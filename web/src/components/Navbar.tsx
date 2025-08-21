import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { listNotifications } from '../api/notifications';
import { today } from '../utils/date';

export default function Navbar() {
  const todayStr = today();
  const { data } = useQuery({
    queryKey: ['notifications', { date: todayStr, state: 'scheduled' }],
    queryFn: () => listNotifications({ date: todayStr, state: 'scheduled' })
  });
  const count = data?.length ?? 0;
  return (
    <nav className="flex items-center justify-between p-4 bg-gray-800 text-white">
      <div className="font-bold">PlanifitAI</div>
      <ul className="flex space-x-4">
        <li><NavLink to="/today">Hoy</NavLink></li>
        <li><NavLink to="/workout">Workout</NavLink></li>
        <li className="relative group">
          <span className="cursor-pointer">Nutrition</span>
          <ul className="absolute left-0 mt-2 hidden w-32 space-y-1 rounded bg-gray-800 p-2 group-hover:block">
            <li><NavLink to="/nutrition/today">Today</NavLink></li>
            <li><NavLink to="/nutrition/plan">Plan</NavLink></li>
          </ul>
        </li>
        <li><NavLink to="/shopping-list">Shopping List</NavLink></li>
        <li><NavLink to="/progress">Progress</NavLink></li>
        <li className="relative">
          <NavLink to="/notifications">Notifications</NavLink>
          {count > 0 && (
            <span className="absolute -right-2 -top-2 rounded-full bg-red-500 px-2 text-xs">{count}</span>
          )}
        </li>
      </ul>
    </nav>
  );
}
