import type { Notification } from "../../api/notifications";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listNotifications, markAsRead } from '../../api/notifications';
import PageHeader from '../../components/layout/PageHeader';
import { today } from '../../utils/date';

export function Notifications() {
  const date = today();
  const qc = useQueryClient();
  const { data } = useQuery<Notification[]>({
    queryKey: ['notifications', date],
    queryFn: () => listNotifications({ status: 'unread', limit: 100, auto: true }),
  });
  const mutation = useMutation({
    mutationFn: (id: number) => markAsRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
  const markAll = useMutation({
    mutationFn: async () => {
      const list = data || [];
      await Promise.all(list.map((n) => markAsRead(n.id)));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
  if (!data) return <div className="p-4">Cargando...</div>;
  if (data.length === 0)
    return (
      <div className="space-y-3 p-4">
        <PageHeader>
          <h1 className="text-xl font-semibold">Notificaciones</h1>
          <p className="text-sm opacity-90">No tienes notificaciones pendientes</p>
        </PageHeader>
      </div>
    );
  return (
    <div className="space-y-4 p-4">
      <PageHeader>
        <h1 className="text-xl font-semibold">Notificaciones</h1>
        <p className="text-sm opacity-90">Recordatorios y avisos</p>
      </PageHeader>
      <div className="text-right">
        <button className="h-10 rounded bg-blue-500 px-4 text-sm text-white" onClick={() => markAll.mutate()}>
          Marcar todo como visto
        </button>
      </div>
      <ul className="space-y-2 text-sm">
        {data.map((n) => {
          const when = new Date(n.scheduled_at_utc);
          const whenTxt = when.toLocaleString('es-ES', {
            weekday: 'short',
            hour: '2-digit',
            minute: '2-digit',
          });
          return (
            <li key={n.id} className="flex items-center justify-between gap-3 rounded border p-2">
              <div>
                <div className="font-medium">{n.title}</div>
                <div className="opacity-80">{n.body}</div>
                <div className="text-xs opacity-60">{whenTxt}</div>
              </div>
              <button className="text-blue-500" onClick={() => mutation.mutate(n.id)}>
                Marcar como visto
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
