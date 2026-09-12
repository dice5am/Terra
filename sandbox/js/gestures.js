/** One-finger orbit + inertia, pinch zoom, double-tap home */

export function attachGestures(el, globe) {
  let dragging = false;
  let lastX = 0, lastY = 0;
  let lastT = 0;
  let vx = 0, vy = 0;
  let pointers = new Map();
  let pinchStartDist = 0;
  let pinchStartZoom = 1;
  let lastTap = 0;

  const pos = (e) => {
    const r = el.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };

  el.addEventListener('pointerdown', (e) => {
    el.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, pos(e));
    if (pointers.size === 1) {
      dragging = true;
      const p = pos(e);
      lastX = p.x; lastY = p.y; lastT = performance.now();
      vx = 0; vy = 0;
      globe.vyaw = 0; globe.vpitch = 0;
      const now = performance.now();
      if (now - lastTap < 320) {
        globe.goHome();
        lastTap = 0;
      } else {
        lastTap = now;
      }
    } else if (pointers.size === 2) {
      dragging = false;
      const pts = [...pointers.values()];
      pinchStartDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
      pinchStartZoom = globe.zoom;
    }
  });

  el.addEventListener('pointermove', (e) => {
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, pos(e));
    if (pointers.size === 2) {
      const pts = [...pointers.values()];
      const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
      if (pinchStartDist > 1) {
        globe.zoom = Math.max(0.72, Math.min(1.85, pinchStartZoom * (dist / pinchStartDist)));
      }
      return;
    }
    if (!dragging) return;
    const p = pos(e);
    const now = performance.now();
    const dt = Math.max(8, now - lastT);
    const dx = p.x - lastX;
    const dy = p.y - lastY;
    globe.orbitBy(dx, dy);
    vx = dx / dt * 16.67;
    vy = dy / dt * 16.67;
    lastX = p.x; lastY = p.y; lastT = now;
  });

  const end = (e) => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinchStartDist = 0;
    if (pointers.size === 0 && dragging) {
      dragging = false;
      // light fling — clamp so no endless spin
      const speed = Math.hypot(vx, vy);
      if (speed > 0.4 && speed < 40) {
        globe.fling(vx, vy);
      }
    }
  };
  el.addEventListener('pointerup', end);
  el.addEventListener('pointercancel', end);

  // Wheel as pinch fallback (desktop)
  el.addEventListener('wheel', (e) => {
    e.preventDefault();
    const f = e.deltaY > 0 ? 0.97 : 1.03;
    globe.pinchScale(f);
  }, { passive: false });
}
