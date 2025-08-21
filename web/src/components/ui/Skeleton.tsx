export function Skeleton({ className }: { className: string }) {
  return (
    <div
      role="status"
      aria-label="loading"
      className={`animate-pulse rounded bg-gray-200 ${className}`}
    />
  );
}
