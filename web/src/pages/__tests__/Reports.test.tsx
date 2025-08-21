import { describe, it, expect, vi, beforeAll } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import ReportsPage from '../Reports';

vi.mock('../../api/routines', () => ({ getUserRoutines: vi.fn().mockResolvedValue([]) }));
vi.mock('../../api/progress', () => ({
  listProgress: vi.fn().mockResolvedValue([]),
  getEntries: vi.fn().mockResolvedValue([]),
}));
vi.mock('../../api/nutrition', () => ({ getSummary: vi.fn().mockResolvedValue([]) }));

beforeAll(() => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (import.meta as any).env.VITE_EXPORT_ENABLED = 'true';
  // polyfill ResizeObserver for recharts
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (window as any).ResizeObserver = ResizeObserver;
});

describe('Reports page', () => {
  it('renders export buttons', async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <ReportsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(await screen.findByText('Exportar CSV')).toBeInTheDocument();
  });
});
