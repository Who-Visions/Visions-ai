import { CCTV_EMBEDS } from './data/cctvEmbeds.js';

/** CCTV lightbox: mirrors the panel's live frame in a resizable, fullscreen-capable window. */
export function installCctvLightbox(root = document) {
  const wrap = root.getElementById('cctv-frame-wrap');
  const source = root.getElementById('cctv-frame');
  const select = root.getElementById('cctv-camera-select');
  if (!wrap || !source) return;

  const box = root.createElement('div');
  box.id = 'cctv-lightbox';
  box.hidden = true;
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.setAttribute('aria-label', 'Live camera');
  box.innerHTML = `
    <div class="cctv-lightbox-window">
      <header class="cctv-lightbox-bar">
        <span class="cctv-lightbox-title"></span>
        <button type="button" data-lightbox="prev" aria-label="Previous camera">‹</button>
        <button type="button" data-lightbox="next" aria-label="Next camera">›</button>
        <button type="button" data-lightbox="fullscreen" aria-label="Toggle full screen">⛶</button>
        <button type="button" data-lightbox="close" aria-label="Close">✕</button>
      </header>
      <img alt="Live camera frame" />
      <iframe title="Live camera player" hidden allow="autoplay; fullscreen"></iframe>
    </div>`;
  root.body.append(box);

  const win = box.querySelector('.cctv-lightbox-window');
  const image = box.querySelector('img');
  const player = box.querySelector('iframe');
  const title = box.querySelector('.cctv-lightbox-title');

  const sync = () => {
    if (box.hidden) return;
    const embed = CCTV_EMBEDS[select?.value];
    image.hidden = Boolean(embed);
    player.hidden = !embed;
    if (embed && player.src !== embed) player.src = embed;
    if (!embed) player.removeAttribute('src');
    if (!embed && source.src) image.src = source.src;
    title.textContent = select?.selectedOptions[0]?.textContent || 'Live camera';
  };
  new MutationObserver(sync).observe(source, { attributes: true, attributeFilter: ['src'] });
  select?.addEventListener('change', sync);

  const close = () => {
    if (root.fullscreenElement === win) root.exitFullscreen();
    box.hidden = true;
    player.removeAttribute('src');
    wrap.focus?.();
  };
  const open = () => {
    box.hidden = false;
    sync();
    box.querySelector('[data-lightbox="close"]').focus();
  };
  const step = (id) => root.getElementById(id)?.click();

  wrap.tabIndex = 0;
  wrap.setAttribute('role', 'button');
  wrap.setAttribute('aria-label', 'Open camera in lightbox');
  wrap.addEventListener('click', open);
  wrap.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open();
  });

  box.addEventListener('click', (event) => {
    if (event.target === box) return close();
    const action = event.target.closest?.('[data-lightbox]')?.dataset.lightbox;
    if (action === 'close') close();
    if (action === 'prev') step('cctv-prev-btn');
    if (action === 'next') step('cctv-next-btn');
    if (action === 'fullscreen') {
      if (root.fullscreenElement === win) root.exitFullscreen();
      else win.requestFullscreen();
    }
    return undefined;
  });
  root.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !box.hidden && !root.fullscreenElement) close();
  });
}
