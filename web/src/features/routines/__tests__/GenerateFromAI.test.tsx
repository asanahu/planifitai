import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import GenerateFromAI from '../GenerateFromAI';
import * as ai from '../../../api/ai';
import * as routines from '../../../api/routines';

describe('GenerateFromAI', () => {
  it('calls AI and creates routine', async () => {
    vi.stubEnv('VITE_FEATURE_AI', '1');
    vi.spyOn(ai, 'generateWorkoutPlanAI').mockResolvedValue({ days: [] });
    const createSpy = vi.spyOn(routines, 'createRoutine').mockResolvedValue({ id: '1', name: '', days: [] });
    vi.spyOn(routines, 'setActiveRoutine').mockResolvedValue(undefined);
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <GenerateFromAI />
        </MemoryRouter>
      </QueryClientProvider>
    );
    await userEvent.click(screen.getAllByText('Generar plan IA')[0]);
    expect(createSpy).toHaveBeenCalled();
  });

  it('uses fallback on error', async () => {
    vi.stubEnv('VITE_FEATURE_AI', '1');
    vi.spyOn(ai, 'generateWorkoutPlanAI').mockRejectedValue(new Error('fail'));
    const createSpy = vi.spyOn(routines, 'createRoutine').mockResolvedValue({ id: '1', name: '', days: [] });
    vi.spyOn(routines, 'setActiveRoutine').mockResolvedValue(undefined);
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <GenerateFromAI />
        </MemoryRouter>
      </QueryClientProvider>
    );
    await userEvent.click(screen.getAllByText('Generar plan IA')[0]);
    expect(createSpy).toHaveBeenCalled();
  });
});
