import * as THREE from 'three';
import '@fontsource-variable/unbounded';
import '@fontsource-variable/onest';
import '@fontsource-variable/jetbrains-mono';
import './desktop.css';
import { createScene, B } from './scene.js';
import { sample, offPose, STOPS, stopAt } from './path.js';
import { createScreens } from './screens.js';
import { createDesktop } from './desktop.js';
import { createKeys } from './keys.js';

const canvas = document.getElementById('scene');
const S = createScene(canvas);
const ui = {
  loader: document.getElementById('loader'),
  bar: document.getElementById('loader-bar'),
  hint: document.getElementById('hint'),
  blocks: [...document.querySelectorAll('[data-stop]')].map((el) => ({ el, i: +el.dataset.stop, a: '', live: false })),
  rail: document.getElementById('rail'),
  scroll: document.getElementById('scroll'),
};
const N = STOPS.length - 1;
const iDesk = STOPS.findIndex((s) => s.id === 'desk');
const shutdownCameraDelay = 1.05;
const shutdownCameraTime = 4.2;

const state = {
  ready: false,
  powered: false,
  shutdownAt: null,
  intro: 0,          // 0 → 1: отъезд камеры от кнопки к общему плану
  p: 0,              // сглаженная прокрутка
  target: 0,
  t: 0,
};
const pose = { pos: new THREE.Vector3(), tgt: new THREE.Vector3(), fov: 30, shift: 0, index: 0, local: 0 };
const cur = { pos: offPose.pos.clone(), tgt: offPose.tgt.clone(), fov: offPose.fov };
const mouse = new THREE.Vector2(), mouseSm = new THREE.Vector2(), mouseRaw = new THREE.Vector2();
const ray = new THREE.Raycaster();
let screens = null, desktop = null, keys = null, button = null, hit = null, accent = '#ff6b4a';

// --- размер: следим сами, а не только по событию окна. Страница может открыться в скрытой
// панели с нулевым размером — тогда без этого холст остаётся чёрным, пока окно не тронут
let sizeW = 0, sizeH = 0;
function fit() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (w === sizeW && h === sizeH) return w > 0 && h > 0;
  sizeW = w; sizeH = h;
  if (w > 0 && h > 0) S.resize();
  return w > 0 && h > 0;
}
history.scrollRestoration = 'manual';
window.scrollTo(0, 0);
fit();

S.load('/models/sborka.glb', (e) => {
  ui.bar.style.transform = `scaleX(${Math.min(1, e.loaded / (e.total || 2.7e6)).toFixed(3)})`;
}).then(async () => {
  // шрифты нужны и странице, и экранам в сцене — ждём их, но не дольше пары секунд
  await Promise.race([
    Promise.all(['600 40px "Unbounded Variable"', '500 20px "Onest Variable"', '500 20px "JetBrains Mono Variable"'].map((f) => document.fonts.load(f, 'Сборка 0123 Aa'))),
    new Promise((r) => setTimeout(r, 2500)),
  ]).catch(() => {});
  screens = await createScreens(S);
  keys = createKeys(S);
  desktop = createDesktop(S, document.getElementById('browser'), {
    setAccent(c) { accent = c; S.setAccent(c); screens.setAccent(c); document.documentElement.style.setProperty('--coral', c); },
    accent: () => accent,
    setTheme: (i) => screens.setTheme(i),
    theme: () => screens.theme,
    setWallpaper: (i) => screens.setWallpaper(i),
    wallpaper: () => screens.wallpaper,
    setBare: (v) => screens.setBare(v),
    powerOff,
  });
  button = S.nodes.power_button;
  hit = new THREE.Mesh(new THREE.SphereGeometry(0.022, 12, 8), new THREE.MeshBasicMaterial({ visible: false }));
  hit.position.copy(B(219, -92, 512));
  S.scene.add(hit);
  // прогрев под заставкой: шейдеры, вся геометрия и тени — до первого показа
  if (!fit()) { S.renderer.setSize(640, 360, false); S.composer.setSize(640, 360); sizeW = sizeH = -1; }
  S.renderer.compile(S.scene, S.camera);
  S.warm();
  state.ready = true;
  document.body.classList.add('ready');
  ui.loader.classList.add('gone');
});

// ---------- включение и выключение

function powerOn() {
  if (!state.ready || state.powered) return;
  state.powered = true;
  S.onSince = state.t;
  document.body.classList.add('powered');
  screens.boot(state.t);
}
function powerOff() {
  if (!state.powered || state.shutdownAt !== null) return;
  state.shutdownAt = state.t;
  state.target = state.p;
  keys.release();
  document.body.classList.add('shutting-down');
}

function finishShutdown() {
  state.shutdownAt = null;
  state.powered = false;
  state.p = state.target = 0;
  S.onSince = null;
  screens.boot(null);
  desktop.reset();
  document.body.classList.remove('powered', 'shutting-down');
  window.scrollTo({ top: 0, behavior: 'instant' });
}

function aim(ev) {
  const r = canvas.getBoundingClientRect();
  mouse.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(mouse, S.camera);
}
// стол «живой», когда камера рядом с остановкой «Стол»
const deskNear = () => (state.powered && state.shutdownAt === null && state.intro >= 1 ? Math.max(0, 1 - Math.abs(state.p * N - iDesk) / 0.45) : 0);

let hoverAt = 0;
canvas.addEventListener('pointermove', (ev) => {
  if (!state.ready) return;
  if (!state.powered) { aim(ev); canvas.style.cursor = hit && ray.intersectObject(hit).length ? 'pointer' : ''; return; }
  if (deskNear() < 0.5) { if (canvas.style.cursor) canvas.style.cursor = ''; return; }
  const now = performance.now();
  if (now - hoverAt < 60) return;      // не чаще ~16 раз в секунду
  hoverAt = now;
  aim(ev);
  const over = ray.intersectObjects(S.nodes.keyboard ? [S.nodes.keyboard] : [], true).length > 0 || keys.hitsMouse(ray);
  canvas.style.cursor = over ? 'pointer' : '';
});
canvas.addEventListener('pointerdown', (ev) => {
  if (!state.ready) return;
  aim(ev);
  if (!state.powered) { if (hit && ray.intersectObject(hit).length) powerOn(); return; }
  if (deskNear() < 0.5) return;
  const k = keys.pick(ray);
  if (k) { if (k.ch) desktop.type(k.ch); return; }
  if (keys.hitsMouse(ray)) keys.click();
});
window.addEventListener('pointerdown', () => { if (keys && state.powered && state.shutdownAt === null) keys.click(); }, true);
window.addEventListener('keydown', (ev) => {
  if (state.shutdownAt !== null || ev.target.closest?.('dialog[open], .quick-nav')) return;
  if (!state.powered) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); powerOn(); } return; }
  if (keys) keys.set(ev.code, true);
});
window.addEventListener('keyup', (ev) => { if (keys) keys.set(ev.code, false); });
window.addEventListener('blur', () => { if (keys) keys.release(); });
ui.hint.addEventListener('click', powerOn);
window.addEventListener('pointermove', (ev) => {
  mouseRaw.set((ev.clientX / window.innerWidth) * 2 - 1, -((ev.clientY / window.innerHeight) * 2 - 1));
}, { passive: true });

// ---------- прокрутка

function readScroll() {
  if (!state.powered || state.shutdownAt !== null) return;
  const max = ui.scroll.offsetHeight - window.innerHeight;
  state.target = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
}
window.addEventListener('scroll', readScroll, { passive: true });
function goTo(i) {
  if (!state.powered || state.shutdownAt !== null) return;
  const max = ui.scroll.offsetHeight - window.innerHeight;
  window.scrollTo({ top: stopAt(i) * max, behavior: 'smooth' });
}
ui.rail.addEventListener('click', (ev) => { const b = ev.target.closest('[data-go]'); if (b) goTo(+b.dataset.go); });

// ---------- кадр

const tmp = new THREE.Vector3();
function frame(dt) {
  state.t += dt;
  const t = state.t;
  const shutdownTime = state.shutdownAt === null ? -1 : t - state.shutdownAt;
  const monitorPower = 1 - THREE.MathUtils.smoothstep(shutdownTime, 0.12, 0.95);
  const casePower = 1 - THREE.MathUtils.smoothstep(shutdownTime, 0.35, 3.8);
  if (shutdownTime >= 0) {
    state.intro = Math.max(0, state.intro - Math.min(dt, Math.max(0, shutdownTime - shutdownCameraDelay)) / shutdownCameraTime);
    if (state.intro === 0) finishShutdown();
  } else if (state.powered) state.intro = Math.min(1, state.intro + dt / 5.2);
  state.p += (state.target - state.p) * (1 - Math.exp(-dt * 3.2));
  sample(state.p, pose);

  // до включения камера у кнопки, после — плавно уходит на путь
  const e = state.intro, ie = e * e * e * (e * (e * 6 - 15) + 10);
  const dock = desktop ? desktop.cameraStillness(state) : 0;
  cur.pos.lerpVectors(offPose.pos, pose.pos, ie);
  cur.tgt.lerpVectors(offPose.tgt, pose.tgt, ie);
  cur.fov = offPose.fov + (pose.fov - offPose.fov) * ie;
  cur.pos.y += Math.sin(ie * Math.PI) * 0.09;
  // лёгкое дыхание камеры и отклик на мышь; у монитора камера неподвижна
  const free = 1 - dock, sway = 0.0035 * free;
  tmp.set(Math.sin(t * 0.31) * sway + mouseSm.x * 0.012 * free, Math.sin(t * 0.23 + 1.3) * sway + mouseSm.y * 0.008 * free, 0);
  S.camera.position.copy(cur.pos);
  S.camera.lookAt(cur.tgt);
  S.camera.translateX(tmp.x);
  S.camera.translateY(tmp.y);
  S.camera.lookAt(cur.tgt);
  // узкие экраны: шире угол, чтобы сцена помещалась по ширине
  const widen = Math.min(3.0, Math.max(1, 1.5 / S.camera.aspect));
  const fov = widen > 1 ? 2 * Math.atan(Math.tan(cur.fov * Math.PI / 360) * widen) * 180 / Math.PI : cur.fov;
  const shift = pose.shift * ie * Math.min(1, S.camera.aspect / 1.5);
  if (Math.abs(fov - S.camera.fov) > 1e-4 || Math.abs(shift - S.camera.filmOffset) > 1e-4) {
    S.camera.fov = fov; S.camera.filmOffset = shift; S.camera.updateProjectionMatrix();
  }

  // кнопка утапливается при нажатии
  if (button) {
    const since = S.onSince == null ? -1 : t - S.onSince;
    const y0 = button.userData.y0 ?? (button.userData.y0 = button.position.y);
    button.position.y = y0 - (since < 0 ? 0 : Math.max(0, 1 - Math.abs(since - 0.08) / 0.12)) * 0.0011;
  }

  S.power = casePower;
  S.update(dt, t);
  if (screens) screens.update(dt, t, monitorPower, casePower);
  if (keys) keys.update(dt, mouseSm.x, mouseSm.y, Math.max(dock, deskNear()));
  if (desktop) desktop.update(state, monitorPower);
  updateText();
  S.render();
}

// подписи разделов: стили меняются, только когда значение действительно изменилось
function updateText() {
  const f = state.p * N;
  const gate = state.shutdownAt !== null || state.intro < 0.86 ? 0 : Math.min(1, (state.intro - 0.86) / 0.14);
  for (const b of ui.blocks) {
    const d = Math.abs(f - b.i);
    const a = (gate * (1 - THREE.MathUtils.smoothstep(d, 0.29, 0.49))).toFixed(2);
    if (a !== b.a) { b.a = a; b.el.style.opacity = a; b.el.style.visibility = a === '0.00' ? 'hidden' : 'visible'; }
    const live = Number(a) > 0.6;
    if (live !== b.live) { b.live = live; b.el.classList.toggle('live', live); }
  }
  const near = String(Math.round(f));
  if (ui.rail.dataset.at !== near) {
    ui.rail.dataset.at = near;
    for (const b of ui.rail.children) b.classList.toggle('on', b.dataset.go === near);
  }
}

// если кадры идут медленно — сначала снижаем разрешение, потом отключаем затенение
let last = performance.now(), slowSum = 0, slowN = 0, level = 0, skip = 0;
function govern(raw) {
  if (state.intro < 1 || document.hidden || raw > 0.25) return;
  slowSum += raw; slowN++;
  if (slowN < 90) return;
  const avg = slowSum / slowN;
  slowSum = 0; slowN = 0;
  if (avg > 1 / 40 && level < 2) {
    level++;
    if (level === 1) { S.renderer.setPixelRatio(1); S.resize(); }
    if (level === 2) S.gtao.enabled = false;
  }
}
function loop(now) {
  requestAnimationFrame(loop);
  if (!fit()) { last = now; return; }
  // пока в окне браузера открыт сайт, сцена рисуется через три кадра на четвёртый: видеокарта нужна сайту
  const busy = desktop && desktop.busy;
  if (busy && (skip = (skip + 1) % 4)) return;
  const raw = (now - last) / 1000;
  last = now;
  if (!busy) govern(raw);
  mouseSm.lerp(mouseRaw, 1 - Math.exp(-Math.min(0.1, raw) * 2.5));
  frame(Math.min(busy ? 0.1 : 0.05, raw));
}
requestAnimationFrame(loop);

// отладочные ручки (панель предпросмотра часто скрыта, и кадры не идут сами)
if (import.meta.env.DEV) {
  window.__sb = {
    S, state, powerOn, powerOff, goTo,
    get desktop() { return desktop; },
    get keys() { return keys; },
    advance(sec, step = 1 / 30) { fit(); for (let x = 0; x < sec; x += step) frame(step); },
    jump(p) { state.target = state.p = p; },
    skipIntro() { powerOn(); state.intro = 1; S.onSince = state.t - 20; screens.boot(state.t - 20); },
  };
}
