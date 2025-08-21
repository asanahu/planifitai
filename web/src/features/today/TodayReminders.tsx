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
    const { routine, day } = routineQuery.data;
    const idx = routine.days.findIndex((d) => d.id === day.id) + 1;
    items.push(`Hoy toca: Entrenamiento ${idx} — ${routine.name}.`);
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
    <section className="rounded border bg-white p-3 shadow-sm dark:bg-gray-800">
      <h2 className="mb-2 flex items-center gap-2 font-semibold text-lg">
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
            className="text-blue-500"
            onClick={() => markAll.mutate()}
            aria-label="Marcar como visto"
          >
            Marcar como visto
          </button>
        )}
        <Link className="text-blue-500" to="/notifications">
          Ver todo
        </Link>
      </div>
    </section>
  );
}

export default TodayReminders;
