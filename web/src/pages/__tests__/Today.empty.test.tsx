import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import TodayPage from '../Today';

vi.mock('../../api/routines', () => ({ getPlannedDayFor: vi.fn().mockResolvedValue(null) }));
vi.mock('../../api/nutrition', () => ({
  getDayLog: vi.fn().mockResolvedValue({ meals: [] }),
  getSummary: vi.fn().mockResolvedValue([]),
}));
vi.mock('../../api/progress', () => ({ listProgress: vi.fn().mockResolvedValue([]) }));

describe('Today page empty state', () => {
  it('shows CTA when no routine or meals', async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <TodayPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    expect(await screen.findByText(/No tienes actividades hoy/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Crear rutina/ })).toBeInTheDocument();
  });
});
