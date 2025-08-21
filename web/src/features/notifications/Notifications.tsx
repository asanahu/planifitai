import type { Notification } from "../../api/notifications";
import { useQuery } from '@tanstack/react-query';
import { listNotifications, readNotification } from '../../api/notifications';

export function Notifications() {
  const { data } = useQuery<Notification[]>({ queryKey: ['notifications'], queryFn: () => listNotifications({ state: 'scheduled' }) });
  if (!data) return <p>Cargando...</p>;
  return (
    <ul className="space-y-2">
      {data.map((n) => (
        <li key={n.id} className="flex justify-between border p-2 rounded">
          <span>{n.message}</span>
          <button className="text-sm text-blue-500" onClick={() => readNotification(n.id)}>Leer</button>
        </li>
      ))}
    </ul>
  );
}
