import { TerraGlobe } from './globe.js';
import { attachGestures } from './gestures.js';

const params = new URLSearchParams(location.search);
const platform = (params.get('platform') || 'ios').toLowerCase() === 'android' ? 'android' : 'ios';
const startMode = (params.get('mode') || 'S1').toUpperCase();

document.body.dataset.platform = platform;
const phone = document.getElementById('phone');
phone.classList.toggle('ios', platform === 'ios');
phone.classList.toggle('android', platform === 'android');

const caps = {
  S0: `S0 Globe only · FRONT · C3 Soft Hollow · no borders · ${platform.toUpperCase()}`,
  S1: `S1 Country lines · FRONT · faint theme-matched borders · default · ${platform.toUpperCase()}`,
  S3: `S3 Elevated glow · FRONT · crystal islands · 2 glow hues · EXAMPLE · ${platform.toUpperCase()}`,
  S5: `S5 Orbit glow · ORBIT ~110° · glow-in-volume spill proof · ${platform.toUpperCase()}`,
};

const canvas = document.getElementById('globe');
const globe = new TerraGlobe(canvas);
const switcher = document.getElementById('switcher');
const capSub = document.getElementById('capSub');

function setMode(m) {
  globe.setMode(m);
  capSub.textContent = caps[m] || caps.S1;
  for (const b of switcher.querySelectorAll('button')) {
    b.classList.toggle('active', b.dataset.mode === m);
  }
  // expose for headless capture
  window.__terraMode = m;
  window.__terraReady = true;
}

switcher.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-mode]');
  if (!btn) return;
  setMode(btn.dataset.mode);
});

attachGestures(canvas, globe);

let last = performance.now();
function loop(t) {
  const dt = Math.min(40, t - last);
  last = t;
  globe.frame(dt);
  requestAnimationFrame(loop);
}

globe.init().then(() => {
  const m = ['S0','S1','S3','S5'].includes(startMode) ? startMode : 'S1';
  // set mode without forcing ease fight on first paint
  const map = { S0: 0, S1: 1, S3: 3, S5: 5 };
  globe.mode = map[m];
  if (m === 'S5') {
    globe.yaw = 210 * Math.PI / 180;
    globe.pitch = -12 * Math.PI / 180;
  } else {
    globe.yaw = 100 * Math.PI / 180;
    globe.pitch = -16 * Math.PI / 180;
  }
  for (const b of switcher.querySelectorAll('button')) {
    b.classList.toggle('active', b.dataset.mode === m);
  }
  capSub.textContent = caps[m];
  window.__terra = globe;
  window.__terraReady = true;
  window.__terraMode = m;
  window.setTerraMode = setMode;
  requestAnimationFrame(loop);
}).catch((err) => {
  console.error(err);
  capSub.textContent = 'WebGL2 init failed: ' + err.message;
});
