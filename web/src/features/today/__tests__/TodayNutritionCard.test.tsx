import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('../../../../api/nutrition', () => ({
  getDayLog: vi.fn().mockResolvedValue({
    totals: { calories: 500 },
    targets: { calories: 1000 },
    meals: [],
  }),
}));
vi.mock('@tanstack/react-query', () => ({
  useQuery: () => ({ data: { totals: { calories: 500 }, targets: { calories: 1000 }, meals: [] }, isLoading: false }),
}));

import { TodayNutritionCard } from '../TodayNutritionCard';

describe('TodayNutritionCard', () => {
  it('shows calories info', async () => {
    render(
      <MemoryRouter>
        <TodayNutritionCard />
      </MemoryRouter>
    );
    expect(screen.getByText(/50% del objetivo/)).toBeInTheDocument();
  });
});
