document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  if (toggle && nav) toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  });

  document.querySelectorAll('.message button').forEach(button => button.addEventListener('click', () => button.parentElement.remove()));
  document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  }));

  document.querySelectorAll('[data-recommendation-id]').forEach(link => link.addEventListener('click', () => {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    if (!token) return;
    fetch(`/api/recommendations/${link.dataset.recommendationId}/click/`, {
      method: 'POST', headers: { 'X-CSRFToken': token, 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    }).catch(() => {});
  }));
});
