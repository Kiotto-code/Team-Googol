export function createModalManager() {
  let activeModal = null;

  function close() {
    if (activeModal) {
      activeModal.remove();
      activeModal = null;
      document.body.style.overflow = '';
    }
  }

  function show({ title, body, actions, size = 'md' }) {
    close();
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.setAttribute('role', 'dialog');
    backdrop.setAttribute('aria-modal', 'true');

    const modal = document.createElement('div');
    modal.className = `modal modal--${size}`;

    const header = document.createElement('div');
    header.className = 'modal__header';

    const titleEl = document.createElement('h2');
    titleEl.className = 'modal__title';
    titleEl.textContent = title || 'Details';
    header.appendChild(titleEl);

    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.textContent = 'Close';
    closeButton.addEventListener('click', close);
    header.appendChild(closeButton);

    modal.appendChild(header);

    const bodyEl = document.createElement('div');
    bodyEl.className = 'modal__body';
    if (typeof body === 'string') {
      bodyEl.innerHTML = body;
    } else if (body instanceof Node) {
      bodyEl.appendChild(body);
    } else if (Array.isArray(body)) {
      body.forEach((node) => bodyEl.appendChild(node));
    }
    modal.appendChild(bodyEl);

    if (actions) {
      const actionsEl = document.createElement('div');
      actionsEl.className = 'modal__actions';
      actions.forEach((action) => actionsEl.appendChild(action));
      modal.appendChild(actionsEl);
    }

    backdrop.appendChild(modal);
    backdrop.addEventListener('click', (event) => {
      if (event.target === backdrop) {
        close();
      }
    });

    document.addEventListener(
      'keydown',
      (event) => {
        if (event.key === 'Escape') {
          close();
        }
      },
      { once: true }
    );

    document.body.appendChild(backdrop);
    document.body.style.overflow = 'hidden';
    activeModal = backdrop;
    closeButton.focus();
    return close;
  }

  return { show, close };
}
