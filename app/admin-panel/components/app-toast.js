const TOAST_DURATION = 5000;
const toastRoot = document.getElementById('toast-root');

if (!toastRoot) {
  throw new Error('Missing toast root element');
}

export function showToast({ title, message, type = 'info', duration = TOAST_DURATION }) {
  const toast = document.createElement('div');
  toast.className = `toast is-${type}`;
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'assertive');

  if (title) {
    const titleEl = document.createElement('div');
    titleEl.className = 'toast__title';
    titleEl.textContent = title;
    toast.appendChild(titleEl);
  }

  if (message) {
    const messageEl = document.createElement('div');
    messageEl.className = 'toast__message';
    messageEl.textContent = message;
    toast.appendChild(messageEl);
  }

  toastRoot.appendChild(toast);

  const timer = window.setTimeout(() => {
    toast.remove();
  }, duration);

  toast.addEventListener('click', () => {
    window.clearTimeout(timer);
    toast.remove();
  });

  return () => {
    window.clearTimeout(timer);
    toast.remove();
  };
}
