import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from '../../App';
import { useAuthStore } from '../../features/auth/useAuthStore';

vi.mock('../../api/users', () => ({ 
  getMe: vi.fn().mockResolvedValue({ profile_completed: false }),
  updateMyProfile: vi.fn().mockResolvedValue({ profile_completed: true })
}));
vi.mock('../../api/routines', () => ({
  getUserRoutines: vi.fn().mockResolvedValue([]),
  getPlannedDayFor: vi.fn().mockResolvedValue(null),
}));
vi.mock('../../api/nutrition', () => ({
  getDayLog: vi.fn().mockResolvedValue({ meals: [] }),
  getSummary: vi.fn().mockResolvedValue([]),
}));
vi.mock('../../api/progress', () => ({ listProgress: vi.fn().mockResolvedValue([]) }));

describe('Onboarding guard', () => {
  it('redirects to onboarding when profile and routine missing', async () => {
    const qc = new QueryClient();
    useAuthStore.setState({ accessToken: 'demo', refreshToken: 'demo' });
    window.history.pushState({}, '', '/today');
    render(
      <QueryClientProvider client={qc}>
        <App />
      </QueryClientProvider>
    );
    expect(await screen.findByText(/Completa tu perfil/)).toBeInTheDocument();
  });

  it('allows access when profile is completed', async () => {
    const qc = new QueryClient();
    useAuthStore.setState({ accessToken: 'demo', refreshToken: 'demo' });
    window.history.pushState({}, '', '/hoy');
    // Mock getMe to return completed profile
    vi.doMock('../../api/users', () => ({ getMe: vi.fn().mockResolvedValue({ profile_completed: true }) }));
    render(
      <QueryClientProvider client={qc}>
        <App />
      </QueryClientProvider>
    );
    expect(
      await screen.findByText(/No tienes actividades hoy/)
    ).toBeInTheDocument();
  });
});
