export function createCodeBlock(code, { language = 'json', label } = {}) {
  const wrapper = document.createElement('div');
  wrapper.className = 'code-block';
  wrapper.setAttribute('role', 'region');
  if (label) {
    wrapper.setAttribute('aria-label', label);
  }

  const pre = document.createElement('pre');
  pre.setAttribute('tabindex', '0');
  pre.textContent = typeof code === 'string' ? code : JSON.stringify(code, null, 2);
  pre.dataset.language = language;
  wrapper.appendChild(pre);
  return wrapper;
}
