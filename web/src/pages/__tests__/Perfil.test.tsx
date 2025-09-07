import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import PerfilPage from '../Perfil';
import { useNavigate } from 'react-router-dom';

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
}));

// Mock the users API
vi.mock('../../api/users', () => ({
  getMe: vi.fn().mockResolvedValue({
    age: null,
    height_cm: null,
    weight_kg: null,
    goal: null,
    activity_level: null,
    profile_completed: false,
  }),
  updateMyProfile: vi.fn().mockResolvedValue({
    age: 30,
    height_cm: 175,
    weight_kg: 70,
    goal: 'maintain',
    activity_level: 'moderate',
    profile_completed: true,
  }),
}));

describe('PerfilPage', () => {
  beforeEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it('renders the profile form with all fields', async () => {
    const navigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(navigate);
    
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={qc}>
        <PerfilPage />
      </QueryClientProvider>
    );

    expect(await screen.findByRole('heading', { name: 'Completa tu perfil' })).toBeInTheDocument();
    expect(screen.getByLabelText('Edad')).toBeInTheDocument();
    expect(screen.getByLabelText('Altura (cm)')).toBeInTheDocument();
    expect(screen.getByLabelText('Peso (kg)')).toBeInTheDocument();
    expect(screen.getByLabelText('Objetivo')).toBeInTheDocument();
    expect(screen.getByLabelText('Nivel de actividad')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Guardar' })).toBeInTheDocument();
  });

  it('validates form fields and shows errors', async () => {
    const navigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(navigate);
    
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={qc}>
        <PerfilPage />
      </QueryClientProvider>
    );

    await screen.findByRole('heading', { name: 'Completa tu perfil' });
    
    // Fill invalid data
    fireEvent.change(screen.getByLabelText('Edad'), { target: { value: '5' } }); // Too young
    fireEvent.change(screen.getByLabelText('Altura (cm)'), { target: { value: '50' } }); // Too short
    fireEvent.change(screen.getByLabelText('Peso (kg)'), { target: { value: '10' } }); // Too light
    
    // Try to submit form
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }));
    
    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/Too small: expected number to be >=14/)).toBeInTheDocument();
    });
  });

  it('submits form successfully and navigates to /hoy', async () => {
    const navigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(navigate);
    
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={qc}>
        <PerfilPage />
      </QueryClientProvider>
    );

    await screen.findByRole('heading', { name: 'Completa tu perfil' });
    
    // Fill form with valid data
    fireEvent.change(screen.getByLabelText('Edad'), { target: { value: '30' } });
    fireEvent.change(screen.getByLabelText('Altura (cm)'), { target: { value: '175' } });
    fireEvent.change(screen.getByLabelText('Peso (kg)'), { target: { value: '70' } });
    fireEvent.change(screen.getByLabelText('Objetivo'), { target: { value: 'maintain' } });
    fireEvent.change(screen.getByLabelText('Nivel de actividad'), { target: { value: 'moderate' } });
    
    // Wait for form to be valid
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Guardar' })).not.toBeDisabled();
    });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }));
    
    // Should navigate to /hoy after successful submission
    await waitFor(() => {
      expect(navigate).toHaveBeenCalledWith('/hoy');
    });
  });

  it('shows goal options correctly', async () => {
    const navigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(navigate);
    
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={qc}>
        <PerfilPage />
      </QueryClientProvider>
    );

    await screen.findByRole('heading', { name: 'Completa tu perfil' });
    
    // Check that goal options are present in the select
    const goalSelect = screen.getByLabelText('Objetivo');
    expect(goalSelect).toBeInTheDocument();
    
    // Check options are rendered
    expect(screen.getByText('Perder peso')).toBeInTheDocument();
    expect(screen.getByText('Mantener')).toBeInTheDocument();
    expect(screen.getByText('Ganar músculo')).toBeInTheDocument();
  });

  it('shows activity level options correctly', async () => {
    const navigate = vi.fn();
    vi.mocked(useNavigate).mockReturnValue(navigate);
    
    const qc = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={qc}>
        <PerfilPage />
      </QueryClientProvider>
    );

    await screen.findByRole('heading', { name: 'Completa tu perfil' });
    
    // Check that activity options are present in the select
    const activitySelect = screen.getByLabelText('Nivel de actividad');
    expect(activitySelect).toBeInTheDocument();
    
    // Check options are rendered
    expect(screen.getByText('Sedentario')).toBeInTheDocument();
    expect(screen.getByText('Ligera')).toBeInTheDocument();
    expect(screen.getByText('Moderada')).toBeInTheDocument();
    expect(screen.getByText('Activa')).toBeInTheDocument();
    expect(screen.getByText('Muy activa')).toBeInTheDocument();
  });
});
