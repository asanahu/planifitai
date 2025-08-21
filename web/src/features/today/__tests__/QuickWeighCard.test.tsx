import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuickWeighCard } from '../QuickWeighCard';
import * as progress from '../../../api/progress';

vi.spyOn(progress, 'listProgress').mockResolvedValue([]);
vi.spyOn(progress, 'createProgressEntry').mockResolvedValue({} as any);
vi.mock('@tanstack/react-query', () => ({
  useQuery: () => ({ data: [], isLoading: false, refetch: vi.fn() }),
  useMutation: (opts: any) => ({ mutate: (v: number) => opts.mutationFn(v) }),
}));

describe('QuickWeighCard', () => {
  it('renders and saves weight', async () => {
    render(<QuickWeighCard />);
    const input = screen.getByPlaceholderText('kg');
    await userEvent.type(input, '80');
    await userEvent.click(screen.getByText('Guardar'));
    expect(progress.createProgressEntry).toHaveBeenCalled();
  });
});
