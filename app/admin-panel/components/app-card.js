export function createCard({
  title,
  icon,
  value,
  meta,
  actions,
  body,
  footer,
  variant = 'default',
} = {}) {
  const card = document.createElement('article');
  card.className = `card card--${variant}`;
  card.setAttribute('tabindex', '0');
  if (title) {
    card.setAttribute('aria-label', title);
  }

  const header = document.createElement('header');
  header.className = 'card__header';

  if (title || icon || actions) {
    const heading = document.createElement('div');
    heading.style.display = 'flex';
    heading.style.alignItems = 'center';
    heading.style.gap = '12px';

    if (icon) {
      const iconEl = document.createElement('span');
      iconEl.className = 'badge';
      iconEl.innerHTML = icon;
      heading.appendChild(iconEl);
    }

    if (title) {
      const titleEl = document.createElement('h3');
      titleEl.className = 'card__title';
      titleEl.textContent = title;
      heading.appendChild(titleEl);
    }

    header.appendChild(heading);
  }

  if (actions) {
    const actionsEl = document.createElement('div');
    actionsEl.className = 'card__actions';
    if (Array.isArray(actions)) {
      actions.forEach((action) => actionsEl.appendChild(action));
    } else {
      actionsEl.appendChild(actions);
    }
    header.appendChild(actionsEl);
  }

  if (header.childElementCount > 0) {
    card.appendChild(header);
  }

  if (value !== undefined) {
    const valueEl = document.createElement('div');
    valueEl.className = 'card__value';
    valueEl.textContent = value;
    card.appendChild(valueEl);
  }

  if (meta) {
    const metaEl = document.createElement('p');
    metaEl.className = 'card__meta';
    metaEl.textContent = meta;
    card.appendChild(metaEl);
  }

  if (body) {
    const bodyEl = document.createElement('div');
    bodyEl.className = 'card__body';
    if (typeof body === 'string') {
      bodyEl.innerHTML = body;
    } else if (body instanceof Node) {
      bodyEl.appendChild(body);
    } else if (Array.isArray(body)) {
      body.forEach((node) => bodyEl.appendChild(node));
    }
    card.appendChild(bodyEl);
  }

  if (footer) {
    const footerEl = document.createElement('footer');
    footerEl.className = 'card__footer';
    if (typeof footer === 'string') {
      footerEl.innerHTML = footer;
    } else if (footer instanceof Node) {
      footerEl.appendChild(footer);
    } else if (Array.isArray(footer)) {
      footer.forEach((node) => footerEl.appendChild(node));
    }
    card.appendChild(footerEl);
  }

  return card;
}
