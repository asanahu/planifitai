import { type ReactNode, useEffect } from 'react';
import DemoBanner from '../components/DemoBanner';
import { seedDemoData } from '../mocks/handlers';
import { worker } from '../mocks/server';

const DEMO = import.meta.env.VITE_DEMO === '1';

export function DemoProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    if (DEMO) {
      seedDemoData();
      worker.start();
      console.info('Demo mode enabled, using mocked API');
    }
  }, []);

  return (
    <>
      {DEMO && <DemoBanner />}
      {children}
    </>
  );
}

export default DemoProvider;
