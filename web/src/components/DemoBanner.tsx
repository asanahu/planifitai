import { resetDemoData } from '../mocks/handlers';

export function DemoBanner() {
  const handleReset = () => {
    resetDemoData();
    window.location.reload();
  };
  return (
    <div className="flex items-center justify-between bg-yellow-100 px-4 py-1 text-sm">
      <span>Demo mode</span>
      <button
        onClick={handleReset}
        className="underline focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Reset demo"
      >
        Reset demo
      </button>
    </div>
  );
}

export default DemoBanner;
