import WeeklyAdherenceChart from '../features/reports/WeeklyAdherenceChart';
import MonthlyProgressChart from '../features/reports/MonthlyProgressChart';
import ReportSummary from '../features/reports/ReportSummary';
import ExportReport from '../features/reports/ExportReport';

export default function ReportsPage() {
  return (
    <div className="space-y-4 p-3 md:p-6">
      <h1 className="text-lg font-semibold">Reportes</h1>
      <WeeklyAdherenceChart />
      <MonthlyProgressChart />
      <ReportSummary />
      <ExportReport />
    </div>
  );
}
