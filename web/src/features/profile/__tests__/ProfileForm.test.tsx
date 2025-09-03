import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProfileForm } from '../ProfileForm';

describe('ProfileForm accordion', () => {
  it('shows goal info when option selected', async () => {
    const user = userEvent.setup();
    render(<ProfileForm />);
    await user.click(screen.getByRole('button', { name: /objetivo/i }));
    await user.selectOptions(screen.getByLabelText('Objetivo'), 'perder_peso');
    expect(screen.getByText(/Reduce peso/)).toBeInTheDocument();
  });

  it('shows activity info when option selected', async () => {
    const user = userEvent.setup();
    render(<ProfileForm />);
    await user.click(screen.getAllByRole('button', { name: /actividad/i })[0]);
    await user.selectOptions(screen.getByLabelText('Actividad'), 'moderada');
    expect(screen.getByText(/Ejercicio moderado/)).toBeInTheDocument();
  });
});
