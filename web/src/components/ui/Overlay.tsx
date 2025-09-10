import type { HTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export default function Overlay({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm',
        className,
      )}
      role="status"
      aria-live="polite"
      {...props}
    >
      <div className="flex flex-col items-center gap-3 rounded-lg bg-white p-6 shadow-soft dark:bg-gray-900">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        <div className="text-sm text-gray-700 dark:text-gray-200">{children || 'Procesando…'}</div>
      </div>
    </div>
  );
}

