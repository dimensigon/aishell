import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from '@components/auth/LoginForm';
import { useAuthStore } from '@store/authStore';

vi.mock('@store/authStore');

describe('LoginForm', () => {
  it('renders login form', () => {
    (useAuthStore as any).mockReturnValue({
      login: vi.fn(),
      isLoading: false,
      error: null,
      clearError: vi.fn(),
    });

    render(
      <BrowserRouter>
        <LoginForm />
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('calls login function on form submit', async () => {
    const mockLogin = vi.fn();
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      isLoading: false,
      error: null,
      clearError: vi.fn(),
    });

    render(
      <BrowserRouter>
        <LoginForm />
      </BrowserRouter>
    );

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'testuser' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123', undefined);
    });
  });

  it('displays error message', () => {
    (useAuthStore as any).mockReturnValue({
      login: vi.fn(),
      isLoading: false,
      error: 'Invalid credentials',
      clearError: vi.fn(),
    });

    render(
      <BrowserRouter>
        <LoginForm />
      </BrowserRouter>
    );

    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
  });
});
