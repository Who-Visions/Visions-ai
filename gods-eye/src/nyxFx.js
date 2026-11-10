/** Nyx UI cursor light: feeds pointer position to glass surfaces as CSS variables. */
const SURFACES = '.nyx-surface, [class*="-inner"], .first-run-card, button';

export function installNyxFx(root = document) {
  let frame = 0;
  let last = null;
  root.addEventListener('pointermove', (event) => {
    last = event;
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      const surface = last.target instanceof Element ? last.target.closest(SURFACES) : null;
      if (!surface) return;
      const rect = surface.getBoundingClientRect();
      surface.style.setProperty('--nyx-x', `${last.clientX - rect.left}px`);
      surface.style.setProperty('--nyx-y', `${last.clientY - rect.top}px`);
    });
  }, { passive: true });
}
