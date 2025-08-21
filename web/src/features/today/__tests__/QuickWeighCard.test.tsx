import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuickWeighCard } from '../QuickWeighCard';
import * as progress from '../../../api/progress';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';

vi.spyOn(progress, 'listProgress').mockResolvedValue([]);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
vi.spyOn(progress, 'createProgressEntry').mockResolvedValue({} as any);

describe('QuickWeighCard', () => {
  it('renders and saves weight', async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <QuickWeighCard />
        </MemoryRouter>
      </QueryClientProvider>
    );
    const input = await screen.findByPlaceholderText('kg');
    await userEvent.type(input, '80');
    await userEvent.click(screen.getByText('Guardar'));
    expect(progress.createProgressEntry).toHaveBeenCalled();
  });
});
