import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { listNotifications, markAsRead } from '../../api/notifications';
import { getPlannedDayFor } from '../../api/routines';
import { getDayLog } from '../../api/nutrition';
import { listProgress } from '../../api/progress';
import { today } from '../../utils/date';
import { Bell } from 'lucide-react';

export function TodayReminders() {
  const date = today();
  const qc = useQueryClient();
  const notifQuery = useQuery({
    queryKey: ['notifications', date],
    queryFn: () => listNotifications({ date, state: 'scheduled|sent_today' }),
  });
  const routineQuery = useQuery({
    queryKey: ['routine-day', date],
    queryFn: () => getPlannedDayFor(new Date(date)),
  });
  const nutritionQuery = useQuery({
    queryKey: ['nutrition', date],
    queryFn: () => getDayLog(date),
  });
  const weightQuery = useQuery({
    queryKey: ['weight', date],
    queryFn: () => listProgress({ metric: 'weight', start: date, end: date }),
  });

  const markAll = useMutation({
    mutationFn: async () => {
      const notifs = notifQuery.data || [];
      await Promise.all(notifs.map((n) => markAsRead(n.id)));
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });

  const items: string[] = [];
  if (routineQuery.data) {
    const anyData: any = routineQuery.data as any;
    const { routine, day, next } = anyData;
    if (day && routine) {
      const idx = routine.days.findIndex((d: any) => d.id === day.id) + 1;
      if (idx > 0) items.push(`Hoy toca: Entrenamiento ${idx} — ${routine.name}.`);
      else items.push(`Hoy toca: ${routine.name}.`);
    } else if (next && routine) {
      const d = new Date(next).toLocaleDateString('es-ES', { weekday: 'long', day: '2-digit', month: 'short' });
      items.push(`Próxima sesión: ${d} — ${routine.name}.`);
    }
  }
  if (nutritionQuery.data?.targets?.calories) {
    items.push(`Objetivo de hoy: ${nutritionQuery.data.targets.calories} kcal. Mantén tu ritmo.`);
  }
  if (weightQuery.data && weightQuery.data.length === 0) {
    items.push('Recuerda anotar tu peso si aún no lo has hecho.');
  }
  (notifQuery.data || []).forEach((n) => items.push(n.message));

  const limited = items.slice(0, 3);
  if (limited.length === 0) return null;

  return (
    <section
      className="rounded border bg-white p-3 shadow-sm dark:bg-gray-800"
      aria-labelledby="today-reminders-heading"
    >
      <h2
        id="today-reminders-heading"
        className="mb-2 flex items-center gap-2 text-lg font-semibold"
      >
        <Bell className="h-5 w-5" /> Recordatorios de hoy
      </h2>
      <ul className="mb-2 list-disc space-y-1 pl-5 text-sm">
        {limited.map((t, i) => (
          <li key={i}>{t}</li>
        ))}
      </ul>
      <div className="flex justify-end gap-4 text-sm">
        {notifQuery.data && notifQuery.data.length > 0 && (
          <button
            className="text-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onClick={() => markAll.mutate()}
            aria-label="Marcar como visto"
          >
            Marcar como visto
          </button>
        )}
        <Link
          className="text-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          to="/notifications"
          aria-label="Ver todas las notificaciones"
        >
          Ver todo
        </Link>
      </div>
    </section>
  );
}

export default TodayReminders;
