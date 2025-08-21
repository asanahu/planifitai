import type { ReactNode } from 'react';

interface KpiCardProps {
  title: string;
  value: string | number;
  subtle?: string;
  icon?: ReactNode;
}

export function KpiCard({ title, value, subtle, icon }: KpiCardProps) {
  return (
    <div
      role="region"
      aria-label={title}
      tabIndex={0}
      className="flex flex-col items-center justify-center rounded border bg-white p-3 text-center text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-gray-800"
    >
      <div className="flex items-center gap-1 text-gray-500 dark:text-gray-400">
        {icon}
        <span>{title}</span>
      </div>
      <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{value}</div>
      {subtle && <div className="text-xs text-gray-500 dark:text-gray-400">{subtle}</div>}
    </div>
  );
}

export default KpiCard;
