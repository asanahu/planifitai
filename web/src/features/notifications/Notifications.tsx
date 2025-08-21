import type { Notification } from "../../api/notifications";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listNotifications, markAsRead } from '../../api/notifications';
import { today } from '../../utils/date';

export function Notifications() {
  const date = today();
  const qc = useQueryClient();
  const { data } = useQuery<Notification[]>({
    queryKey: ['notifications', { date, state: 'scheduled' }],
    queryFn: () => listNotifications({ date, state: 'scheduled' }),
  });
  const mutation = useMutation({
    mutationFn: (id: string) => markAsRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
  if (!data) return <p>Cargando...</p>;
  if (data.length === 0) return <p>Sin notificaciones</p>;
  return (
    <ul className="space-y-2">
      {data.map((n) => (
        <li key={n.id} className="flex justify-between border p-2 rounded">
          <span>{n.message}</span>
          <button className="text-sm text-blue-500" onClick={() => mutation.mutate(n.id)}>Leer</button>
        </li>
      ))}
    </ul>
  );
}
