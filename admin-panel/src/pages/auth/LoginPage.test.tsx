import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginPage } from './LoginPage';

const mocks = vi.hoisted(() => ({
  loginMock: vi.fn(),
  navigateMock: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn()
}));

let consoleErrorSpy: ReturnType<typeof vi.spyOn> | undefined;

vi.mock('@/store/auth', () => ({
  useAuthStore: <T,>(selector: (state: { login: typeof mocks.loginMock; isLoading: boolean }) => T) =>
    selector({
      login: mocks.loginMock,
      isLoading: false
    })
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mocks.navigateMock
  };
});

vi.mock('sonner', () => ({
  toast: {
    success: mocks.toastSuccess,
    error: mocks.toastError
  }
}));

describe('LoginPage', () => {
  beforeEach(() => {
    mocks.loginMock.mockReset();
    mocks.navigateMock.mockReset();
    mocks.toastSuccess.mockReset();
    mocks.toastError.mockReset();
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy?.mockRestore();
  });

  it('logs in successfully and redirects', async () => {
    mocks.loginMock.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();

    render(<LoginPage />);

    const submitButtons = screen.getAllByRole('button', { name: 'login.submit' });
    const submitButton = submitButtons[submitButtons.length - 1];
    const form = submitButton.closest('form');
    if (!form) {
      throw new Error('Expected submit button to be inside a form');
    }
    const emailInput = form.querySelector('input[name="email"]') as HTMLInputElement | null;
    const passwordInput = form.querySelector('input[name="password"]') as HTMLInputElement | null;
    if (!emailInput || !passwordInput) {
      throw new Error('Form inputs not found');
    }

    fireEvent.change(emailInput, { target: { value: 'admin@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    await user.click(submitButton);

    await waitFor(() => expect(mocks.loginMock).toHaveBeenCalledWith({ email: 'admin@example.com', password: 'password123' }));
    expect(mocks.toastSuccess).toHaveBeenCalledWith('login.title');
    expect(mocks.navigateMock).toHaveBeenCalledWith('/');
  });

  it('surfaces an error toast when login fails', async () => {
    mocks.loginMock.mockRejectedValueOnce(new Error('Invalid credentials'));
    const user = userEvent.setup();

    render(<LoginPage />);

    const submitButtons = screen.getAllByRole('button', { name: 'login.submit' });
    const submitButton = submitButtons[submitButtons.length - 1];
    const form = submitButton.closest('form');
    if (!form) {
      throw new Error('Expected submit button to be inside a form');
    }
    const emailInput = form.querySelector('input[name="email"]') as HTMLInputElement | null;
    const passwordInput = form.querySelector('input[name="password"]') as HTMLInputElement | null;
    if (!emailInput || !passwordInput) {
      throw new Error('Form inputs not found');
    }

    fireEvent.change(emailInput, { target: { value: 'admin@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });

    await user.click(submitButton);

    await waitFor(() => expect(mocks.loginMock).toHaveBeenCalled());
    await waitFor(() => expect(mocks.toastError).toHaveBeenCalledWith('Invalid credentials'));
    expect(mocks.navigateMock).not.toHaveBeenCalled();
  });
});
