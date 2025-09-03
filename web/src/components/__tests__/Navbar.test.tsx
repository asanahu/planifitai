import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import Navbar from '../Navbar';

vi.mock('../../api/notifications', () => ({
  listNotifications: vi.fn().mockResolvedValue([]),
}));

const logout = vi.fn();
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({ user: { id: '1', name: 'Test' }, logout }),
}));

describe('Navbar logout', () => {
  it('calls logout when clicking button', async () => {
    const user = userEvent.setup();
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <BrowserRouter>
          <Navbar />
        </BrowserRouter>
      </QueryClientProvider>
    );
    await user.click(screen.getByRole('button', { name: /logout/i }));
    expect(logout).toHaveBeenCalled();
  });
});
