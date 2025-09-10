import type { HTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export default function PageHeader({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-xl bg-hero-gradient p-4 text-white shadow-soft md:p-6',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

