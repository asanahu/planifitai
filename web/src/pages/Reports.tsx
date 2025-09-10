import { Suspense, lazy } from 'react';
import ReportSummary from '../features/reports/ReportSummary';
import ExportReport from '../features/reports/ExportReport';
import { useQuery } from '@tanstack/react-query';
import { listProgress } from '../api/progress';
import { getSummary } from '../api/nutrition';
import { today, daysAgo } from '../utils/date';
import { Link } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';

const WeeklyAdherenceChart = lazy(() => import('../features/reports/WeeklyAdherenceChart'));
const MonthlyProgressChart = lazy(() => import('../features/reports/MonthlyProgressChart'));

export default function ReportsPage() {
  const start = daysAgo(7);
  const end = today();
  const weightQ = useQuery({ queryKey: ['report-weight', start, end], queryFn: () => listProgress({ metric: 'weight', start, end }) });
  const nutriQ = useQuery({ queryKey: ['report-nut', start, end], queryFn: () => getSummary(start, end) });
  if ((weightQ.data?.length || 0) === 0 && (nutriQ.data?.length || 0) === 0) {
    return (
      <div className="space-y-2 p-3">
        <p>Aún no hay datos para graficar.</p>
        <Link
          to="/today"
          role="button"
          aria-label="Ir a hoy"
          tabIndex={0}
          className="inline-block rounded border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-sky-400"
        >
          Ir a hoy
        </Link>
      </div>
    );
  }
  return (
    <div className="space-y-4 p-3 md:p-6">
      <PageHeader>
        <h1 className="text-xl font-semibold">Reportes</h1>
        <p className="text-sm opacity-90">Tendencias y métricas agregadas</p>
      </PageHeader>
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
