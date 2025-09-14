import * as React from "react"

const Progress = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { value?: number | null }>(({ className, value, ...props }, ref) => {
  const progressValue = value ?? 0;

  return (
    <div
      ref={ref}
      className={`relative h-4 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700 ${className}`}
      {...props}
    >
      <div
        className="h-full w-full flex-1 bg-blue-500 transition-all"
        style={{ transform: `translateX(-${100 - (progressValue || 0)}%)` }}
      />
    </div>
  )
})
Progress.displayName = "Progress"

export { Progress }