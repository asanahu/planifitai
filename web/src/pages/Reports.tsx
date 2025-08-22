import { Suspense, lazy } from 'react';
import ReportSummary from '../features/reports/ReportSummary';
import ExportReport from '../features/reports/ExportReport';
import { useQuery } from '@tanstack/react-query';
import { listProgress } from '../api/progress';
import { getSummary } from '../api/nutrition';
import { today, daysAgo } from '../utils/date';

const WeeklyAdherenceChart = lazy(() => import('../features/reports/WeeklyAdherenceChart'));
const MonthlyProgressChart = lazy(() => import('../features/reports/MonthlyProgressChart'));

export default function ReportsPage() {
  const start = daysAgo(7);
  const end = today();
  const weightQ = useQuery({ queryKey: ['report-weight', start, end], queryFn: () => listProgress({ metric: 'weight', start, end }) });
  const nutriQ = useQuery({ queryKey: ['report-nut', start, end], queryFn: () => getSummary(start, end) });
  if ((weightQ.data?.length || 0) === 0 && (nutriQ.data?.length || 0) === 0) {
    return (
      <div className="p-3">Aún no hay datos para graficar. Registra peso o calorías esta semana</div>
    );
  }
  return (
    <div className="space-y-4 p-3 md:p-6">
      <h1 className="text-lg font-semibold">Reportes</h1>
      <Suspense fallback={<div />}>
        <WeeklyAdherenceChart />
      </Suspense>
      <Suspense fallback={<div />}>
        <MonthlyProgressChart />
      </Suspense>
      <ReportSummary />
      <ExportReport />
    </div>
  );
}
