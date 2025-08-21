import { useQuery } from '@tanstack/react-query';
import { getEntries } from '../../api/progress';
import { getSummary } from '../../api/nutrition';
import { today, daysAgo } from '../../utils/date';

export default function ExportReport() {
  const enabled = import.meta.env.VITE_EXPORT_ENABLED !== 'false';
  const end = today();
  const start = daysAgo(30);
  const weightQ = useQuery({
    queryKey: ['progress', 'weight', start, end],
    queryFn: () => getEntries('weight', start, end),
    enabled,
  });
  const caloriesQ = useQuery({
    queryKey: ['nutrition-summary', start, end],
    queryFn: () => getSummary(start, end),
    enabled,
  });
  if (!enabled) return null;

  const exportCsv = () => {
    const lines = ['date,weight,calories'];
    const map: Record<string, { weight?: number; calories?: number }> = {};
    (weightQ.data || []).forEach((w: { date: string; value: number }) => {
      map[w.date] = { ...map[w.date], weight: w.value };
    });
    (caloriesQ.data || []).forEach((c: { date: string; calories: number }) => {
      map[c.date] = { ...map[c.date], calories: c.calories };
    });
    Object.keys(map).forEach((d) =>
      lines.push(`${d},${map[d].weight ?? ''},${map[d].calories ?? ''}`)
    );
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'report.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportPdf = () => {
    window.print();
  };

  return (
    <div className="flex gap-2 mt-2">
      <button
        className="rounded bg-blue-500 px-3 py-1 text-white"
        onClick={exportCsv}
        aria-label="Exportar CSV"
      >
        Exportar CSV
      </button>
      <button
        className="rounded bg-blue-500 px-3 py-1 text-white"
        onClick={exportPdf}
        aria-label="Exportar PDF"
      >
        Exportar PDF
      </button>
    </div>
  );
}
