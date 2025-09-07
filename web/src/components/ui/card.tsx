import type { HTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-lg border border-gray-200 bg-white p-6 shadow-soft dark:border-gray-800 dark:bg-gray-900',
        className,
      )}
      {...props}
    />
  );
}

export default Card;
