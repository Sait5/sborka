// Рабочий стол на мониторе: настоящая вёрстка, натянутая на экран в сцене.
// Значки, панель задач, меню и окна программ; сайты проектов открываются в окне браузера.
import * as THREE from 'three';
import { STOPS } from './path.js';
import { WALLPAPERS, THEMES, LAYOUT } from './screens.js';

import { PROJECTS } from './projects.js';
const ACCENTS = ['#ff6b4a', '#ffae3b', '#59e39b', '#46c8ff', '#8f7bff', '#ff5fa2', '#f2f4f8'];
const ABOUT = `Привет. Я Сейт-Ахмет, фронтенд-разработчик.

Делаю сайты и программы, которые хочется трогать: 3D-сцены, свои инструменты, интерфейсы.

Стек: React, Vue, Next.js, Nuxt, TypeScript, three.js, Node.js.

Написать мне:
Telegram — @Saitama000001
GitHub — github.com/Sait5
Почта — balaevs134@gmail.com

Этот текст можно править: печатай на своей клавиатуре или нажимай клавиши на столе.`;

const W = 1280, H = 720, K = W / 1920;
const sv = (d, extra = '') => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ${extra}>${d}</svg>`;
const I = {
  back: sv('<path d="M15 5l-7 7 7 7"/>'), fwd: sv('<path d="M9 5l7 7-7 7"/>'),
  reload: sv('<path d="M20 12a8 8 0 1 1-2.4-5.7"/><path d="M20 4v5h-5"/>'), home: sv('<path d="M4 11l8-7 8 7"/><path d="M6 10v9h12v-9"/>'),
  ext: sv('<path d="M14 5h5v5"/><path d="M19 5l-8 8"/><path d="M17 14v5H5V7h5"/>'), plus: sv('<path d="M12 5v14M5 12h14"/>'),
  close: sv('<path d="M6 6l12 12M18 6L6 18"/>'), min: sv('<path d="M6 12h12"/>'), max: sv('<rect x="6" y="6" width="12" height="12" rx="1.5"/>'),
  search: sv('<circle cx="11" cy="11" r="6"/><path d="M16 16l4 4"/>'), lock: sv('<rect x="6" y="11" width="12" height="8" rx="2"/><path d="M9 11V8a3 3 0 0 1 6 0v3"/>'),
  power: sv('<path d="M7.5 6.5a7.5 7.5 0 1 0 9 0"/><path d="M12 3v8"/>'),
  folder: '<svg viewBox="0 0 24 24"><path d="M2.5 6.5a2 2 0 0 1 2-2h4.2l2 2.2H19.5a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2z" fill="#e9a54d"/><path d="M2.5 10h19v8a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2z" fill="#f5bd6a"/></svg>',
  note: '<svg viewBox="0 0 24 24"><rect x="5" y="2.5" width="14" height="19" rx="2" fill="#e8ebf2"/><path d="M8 8h8M8 11.5h8M8 15h5" stroke="#9aa0ac" stroke-width="1.5" stroke-linecap="round"/></svg>',
};
const APPS = {
  vivid: { title: 'Vivid', label: 'Vivid', img: '/icons/vivid.png', w: 600, h: 400 },
  cooler: { title: 'CoolerScreen', label: 'CoolerScreen', img: '/icons/coolerscreen.png', w: 560, h: 430 },
  horizon: { title: 'Horizon', label: 'Horizon', img: '/icons/horizon.png', w: 1040, h: 580 },
  projects: { title: 'Проекты', label: 'Проекты', svg: I.folder, w: 620, h: 470 },
  note: { title: 'обо мне.txt — Блокнот', label: 'обо мне.txt', svg: I.note, w: 560, h: 440 },
};
const ico = (a, cls = '') => a.img ? `<img class="${cls}" src="${a.img}" alt="" draggable="false" />` : `<span class="${cls} svgi">${a.svg}</span>`;

// проективное преобразование прямоугольника W×H в четырёхугольник на экране
function adj(m) {
  return [m[4] * m[8] - m[5] * m[7], m[2] * m[7] - m[1] * m[8], m[1] * m[5] - m[2] * m[4],
    m[5] * m[6] - m[3] * m[8], m[0] * m[8] - m[2] * m[6], m[2] * m[3] - m[0] * m[5],
    m[3] * m[7] - m[4] * m[6], m[1] * m[6] - m[0] * m[7], m[0] * m[4] - m[1] * m[3]];
}
function mm(a, b) {
  const c = Array(9);
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) { let s = 0; for (let k = 0; k < 3; k++) s += a[3 * i + k] * b[3 * k + j]; c[3 * i + j] = s; }
  return c;
}
const mv = (m, v) => [m[0] * v[0] + m[1] * v[1] + m[2] * v[2], m[3] * v[0] + m[4] * v[1] + m[5] * v[2], m[6] * v[0] + m[7] * v[1] + m[8] * v[2]];
function basis(p) {
  const m = [p[0][0], p[1][0], p[2][0], p[0][1], p[1][1], p[2][1], 1, 1, 1];
  const v = mv(adj(m), [p[3][0], p[3][1], 1]);
  return mm(m, [v[0], 0, 0, 0, v[1], 0, 0, 0, v[2]]);
}
const SRC = adj(basis([[0, 0], [W, 0], [0, H], [W, H]]));
function homography(dst) {
  const t = mm(basis(dst), SRC);
  for (let i = 0; i < 9; i++) t[i] /= t[8];
  return `matrix3d(${t[0]},${t[3]},0,${t[6]},${t[1]},${t[4]},0,${t[7]},0,0,1,0,${t[2]},${t[5]},0,${t[8]})`;
}

export function createDesktop(S, root, hooks) {
  // --- углы экрана по развёртке
  const mesh = S.screens.screen_monitor;
  const pos = mesh.geometry.attributes.position, uv = mesh.geometry.attributes.uv;
  const bb = new THREE.Box3().setFromBufferAttribute(pos), ctr = bb.getCenter(new THREE.Vector3()), size = bb.getSize(new THREE.Vector3());
  let uc = 0, vc = 0;
  for (let i = 0; i < uv.count; i++) { uc += uv.getX(i) / uv.count; vc += uv.getY(i) / uv.count; }
  const du = new THREE.Vector3(), dv = new THREE.Vector3(), p = new THREE.Vector3();
  for (let i = 0; i < uv.count; i++) { p.fromBufferAttribute(pos, i).sub(ctr); du.addScaledVector(p, uv.getX(i) - uc); dv.addScaledVector(p, uv.getY(i) - vc); }
  du.normalize(); dv.normalize();
  const ext = (d) => Math.abs(d.x) * size.x / 2 + Math.abs(d.y) * size.y / 2 + Math.abs(d.z) * size.z / 2;
  const quad = [[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([a, b]) => ctr.clone().addScaledVector(du, a * ext(du)).addScaledVector(dv, b * ext(dv)));

  // --- каркас рабочего стола
  const L = LAYOUT, order = ['vivid', 'cooler', 'horizon', 'projects', 'note'];
  root.innerHTML = `
    <div class="dk" id="dk">
      <div class="dk-icons">${order.map((id, i) => `<button class="dk-ic" data-open="${id}" style="left:${L.icon.x * K - 14}px;top:${(L.icon.y + i * L.icon.step) * K}px">${ico(APPS[id], 'dk-im')}<span>${APPS[id].label}</span></button>`).join('')}</div>
      <div id="wins"></div>
      <div class="dk-menu" id="menu">
        <div class="mn-head"><b>Балаев Сейт-Ахмет</b><span>фронтенд-разработчик</span></div>
        <a href="https://t.me/Saitama000001" target="_blank" rel="noopener"><span>Telegram</span><b>@Saitama000001</b></a>
        <a href="https://github.com/Sait5" target="_blank" rel="noopener"><span>GitHub</span><b>Sait5</b></a>
        <a href="mailto:balaevs134@gmail.com"><span>Почта</span><b>balaevs134@gmail.com</b></a>
        <button class="mn-off" id="off">${I.power}<span>Выключить компьютер</span></button>
      </div>
      <div class="dk-bar" style="left:${L.bar.x * K}px;top:${L.bar.y * K}px;width:${L.bar.w * K}px;height:${L.bar.h * K}px">
        <button class="tb-start" id="start" title="Меню"><i></i><i></i><i></i><i></i></button>
        <label class="tb-search">${I.search}<input id="q" placeholder="Поиск" autocomplete="off" spellcheck="false" /></label>
        <div class="tb-apps">${order.map((id) => `<button class="tb-app" data-task="${id}" title="${APPS[id].label}">${ico(APPS[id], 'tb-im')}</button>`).join('')}</div>
        <div class="tb-clock" id="clk"></div>
      </div>
    </div>`;
  const $ = (id) => root.querySelector('#' + id);
  const dk = $('dk'), wins = $('wins'), menu = $('menu'), clk = $('clk'), q = $('q');
  const open = new Map();
  let z = 10, active = null;

  // --- окна
  function focus(id) {
    active = id;
    for (const [k, w] of open) w.classList.toggle('on', k === id);
    if (id) open.get(id).style.zIndex = ++z;
    root.querySelectorAll('.tb-app').forEach((b) => { b.classList.toggle('run', open.has(b.dataset.task)); b.classList.toggle('on', b.dataset.task === id && !open.get(id).classList.contains('hid')); });
  }
  function close(id) { const w = open.get(id); if (!w) return; w.remove(); open.delete(id); focus(null); }
  function launch(id) {
    menu.classList.remove('show');
    let w = open.get(id);
    if (w) { w.classList.remove('hid'); focus(id); return w; }
    const a = APPS[id], n = open.size;
    w = document.createElement('div');
    w.className = 'w';
    w.dataset.app = id;
    w.style.cssText = `width:${a.w}px;height:${a.h}px;left:${Math.max(90, (W - a.w) / 2 + n * 22)}px;top:${Math.max(14, (H - 60 - a.h) / 2 + n * 16)}px`;
    w.innerHTML = `<div class="w-top">${ico(a, 'w-ic')}<span class="w-title">${a.title}</span><button class="w-b" data-act="min" title="Свернуть">${I.min}</button><button class="w-b" data-act="max" title="Развернуть">${I.max}</button><button class="w-b x" data-act="close" title="Закрыть">${I.close}</button></div><div class="w-body"></div>`;
    wins.appendChild(w);
    open.set(id, w);
    BODY[id](w.querySelector('.w-body'), w);
    requestAnimationFrame(() => w.classList.add('in'));
    focus(id);
    return w;
  }
  // перетаскивание за заголовок: смещение указателя переводится в масштаб экрана
  let drag = null;
  wins.addEventListener('pointerdown', (e) => {
    const w = e.target.closest('.w');
    if (!w) return;
    focus(w.dataset.app);
    const act = e.target.closest('[data-act]')?.dataset.act;
    if (act === 'close') return close(w.dataset.app);
    if (act === 'min') { w.classList.add('hid'); return focus(null); }
    if (act === 'max') return w.classList.toggle('max');
    if (!e.target.closest('.w-top') || w.classList.contains('max')) return;
    const k = root.getBoundingClientRect().width / W || 1;
    drag = { w, x: e.clientX, y: e.clientY, l: w.offsetLeft, t: w.offsetTop, k };
    wins.setPointerCapture(e.pointerId);
    w.classList.add('drag');
  });
  wins.addEventListener('pointermove', (e) => {
    if (!drag) return;
    drag.w.style.left = Math.min(W - 80, Math.max(-drag.w.offsetWidth + 120, drag.l + (e.clientX - drag.x) / drag.k)) + 'px';
    drag.w.style.top = Math.min(H - 90, Math.max(0, drag.t + (e.clientY - drag.y) / drag.k)) + 'px';
  });
  const drop = () => { if (drag) { drag.w.classList.remove('drag'); drag = null; } };
  wins.addEventListener('pointerup', drop);
  wins.addEventListener('pointercancel', drop);

  // --- содержимое программ
  let showSite = null;
  const BODY = {
    horizon(el) {
      el.innerHTML = `
        <div class="tabs"><div class="tabstrip" id="tabstrip"></div><button class="nav plus" id="plus" title="Новая вкладка">${I.plus}</button></div>
        <div class="bar">
          <button class="nav" id="bk" title="Назад">${I.back}</button><button class="nav" disabled title="Вперёд">${I.fwd}</button>
          <button class="nav" id="rl" title="Обновить">${I.reload}</button><button class="nav" id="hm" title="Домой">${I.home}</button>
          <div class="url"><span class="lk">${I.lock}</span><span id="url"></span></div>
          <a class="nav" id="ext" target="_blank" rel="noopener" title="Открыть в отдельной вкладке">${I.ext}</a>
        </div>
        <div class="view">
          <div class="start" id="startpg">
            <div class="start-head"><div class="start-title">Мои работы</div><div class="start-sub">Нажми — сайт откроется прямо в этом окне</div></div>
            <div class="grid">${PROJECTS.map((p, i) => `<button class="tile" data-i="${i}"><span class="shot" style="background-image:url(/shots/${p.id}.jpg)"></span><span class="meta"><b><i class="fav" style="background:${p.c}">${p.name[0]}</i>${p.name}${p.external ? ' ↗' : ''}</b><span>${p.note}</span><em>${p.stack}</em></span></button>`).join('')}</div>
          </div>
          <iframe id="frame" title="Сайт проекта" referrerpolicy="no-referrer"></iframe>
          <div class="load" id="load"><div class="load-ring"></div><b id="load-name"></b><span>Загружаю сайт…</span></div>
        </div>`;
      const g = (id) => el.querySelector('#' + id);
      const strip = g('tabstrip'), url = g('url'), frame = g('frame'), start = g('startpg'), ex = g('ext'), load = g('load');
      let cur = -1, timer = 0;
      frame.addEventListener('load', () => { clearTimeout(timer); load.classList.remove('on'); });
      const show = (i) => {
        cur = i;
        const pr = PROJECTS[i];
        strip.innerHTML = `<button class="tab ${pr ? '' : 'on'}" data-i="-1"><img class="fav" src="/icons/horizon.png" alt="" />Новая вкладка</button>` +
          (pr ? `<button class="tab on" data-i="${i}"><i class="fav" style="background:${pr.c}">${pr.name[0]}</i>${pr.name}<span class="x" data-close="1">${I.close}</span></button>` : '');
        url.textContent = pr ? pr.url.replace('https://', '') : 'horizon://start';
        ex.style.visibility = pr ? 'visible' : 'hidden';
        if (pr) {
          ex.href = pr.url;
          if (frame.dataset.src !== pr.url) {
            g('load-name').textContent = pr.name;
            load.style.backgroundImage = `linear-gradient(rgba(8,9,12,.82),rgba(8,9,12,.92)),url(/shots/${pr.id}.jpg)`;
            load.classList.add('on');
            clearTimeout(timer);
            timer = setTimeout(() => load.classList.remove('on'), 15000);
            frame.src = pr.url; frame.dataset.src = pr.url;
          }
        } else { frame.removeAttribute('src'); frame.dataset.src = ''; load.classList.remove('on'); }
        frame.classList.toggle('on', !!pr);
        start.classList.toggle('off', !!pr);
        api.site = !!pr;
      };
      showSite = (i) => { const pr = PROJECTS[i]; if (pr && pr.external) window.open(pr.url, '_blank', 'noopener'); else show(i); };
      show(-1);
      el.querySelector('.grid').addEventListener('click', (e) => { const b = e.target.closest('.tile'); if (b) showSite(+b.dataset.i); });
      strip.addEventListener('click', (e) => { if (e.target.closest('[data-close]') || +e.target.closest('.tab')?.dataset.i < 0) show(-1); });
      for (const id of ['bk', 'hm', 'plus']) g(id).addEventListener('click', () => show(-1));
      g('rl').addEventListener('click', () => { if (cur >= 0) { frame.dataset.src = ''; show(cur); } });
    },
    projects(el) {
      el.innerHTML = `<div class="ex">${PROJECTS.map((p, i) => `<button class="ex-row" data-i="${i}"><span class="ex-th" style="background-image:url(/shots/${p.id}.jpg)"></span><b>${p.name}</b><span>${p.note}</span><em>${p.stack}</em></button>`).join('')}</div>`;
      el.addEventListener('click', (e) => { const b = e.target.closest('.ex-row'); if (!b) return; launch('horizon'); showSite(+b.dataset.i); });
    },
    vivid(el) {
      const hues = ['#3a1d18', '#16263f', '#1d3320', '#2c1a40'];
      el.innerHTML = `<div class="pane"><div class="pane-h">Обои рабочего стола</div><div class="wp">${WALLPAPERS.map((w, i) => `<button class="wp-i" data-i="${i}"><span style="background:linear-gradient(#06080e 30%,${hues[i]})"></span><b>${w.name}</b></button>`).join('')}</div><p class="pane-n">Живые обои для Windows: видео, GIF, сцены с частицами. Здесь можно сменить оттенок обоев на этом мониторе.</p></div>`;
      const mark = () => el.querySelectorAll('.wp-i').forEach((b) => b.classList.toggle('on', +b.dataset.i === hooks.wallpaper()));
      el.addEventListener('click', (e) => { const b = e.target.closest('.wp-i'); if (b) { hooks.setWallpaper(+b.dataset.i); mark(); } });
      mark();
    },
    cooler(el) {
      el.innerHTML = `<div class="pane"><div class="pane-h">Тема экрана на водоблоке</div><div class="th">${THEMES.map((t, i) => `<button class="th-i" data-t="${i}">${t}</button>`).join('')}</div>
        <div class="pane-h">Цвет подсветки компьютера</div><div class="sw">${ACCENTS.map((c) => `<button class="sw-i" data-c="${c}" style="background:${c}" title="${c}"></button>`).join('')}</div>
        <p class="pane-n">Программа для экрана на помпе водяного охлаждения. Выбери тему и цвет — они сразу применятся к компьютеру: пролистай назад и посмотри.</p></div>`;
      const mark = () => { el.querySelectorAll('.th-i').forEach((b) => b.classList.toggle('on', +b.dataset.t === hooks.theme())); el.querySelectorAll('.sw-i').forEach((b) => b.classList.toggle('on', b.dataset.c === hooks.accent())); };
      el.addEventListener('click', (e) => {
        const t = e.target.closest('.th-i'), c = e.target.closest('.sw-i');
        if (t) hooks.setTheme(+t.dataset.t);
        if (c) hooks.setAccent(c.dataset.c);
        mark();
      });
      mark();
    },
    note(el) {
      el.innerHTML = '<textarea class="np" id="np" spellcheck="false"></textarea>';
      el.firstChild.value = ABOUT;
    },
  };

  // --- значки, панель задач, меню
  dk.addEventListener('click', (e) => {
    const o = e.target.closest('[data-open]'), t = e.target.closest('[data-task]');
    if (o) launch(o.dataset.open);
    if (t) {
      const id = t.dataset.task, w = open.get(id);
      if (w && active === id && !w.classList.contains('hid')) { w.classList.add('hid'); focus(null); } else launch(id);
    }
    if (e.target.closest('#start')) menu.classList.toggle('show');
    else if (!e.target.closest('#menu')) menu.classList.remove('show');
    if (e.target.closest('#off')) { menu.classList.remove('show'); hooks.powerOff(); }
  });
  // поиск по названиям: Enter открывает программу или проект
  q.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const s = q.value.trim().toLowerCase();
    if (!s) return;
    const app = order.find((id) => APPS[id].label.toLowerCase().includes(s));
    const pr = PROJECTS.findIndex((x) => x.name.toLowerCase().includes(s));
    if (app) launch(app); else if (pr >= 0) { launch('horizon'); showSite(pr); }
    q.value = '';
  });
  let minute = -1;
  function tick() {
    const d = new Date();
    if (d.getMinutes() === minute) return;
    minute = d.getMinutes();
    clk.innerHTML = `<b>${String(d.getHours()).padStart(2, '0')}:${String(minute).padStart(2, '0')}</b><span>${d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })}</span>`;
  }

  const iMon = STOPS.findIndex((s) => s.id === 'monitor'), iDesk = STOPS.findIndex((s) => s.id === 'desk');
  function screenDistance(state) {
    const f = state.p * (STOPS.length - 1);
    return Math.max(iMon - f, f - iDesk, 0);
  }
  const v = new THREE.Vector3();
  let lastT = '', shown = false;
  const api = {
    site: false, busy: false,
    launch,
    cameraStillness(state) {
      if (!state.powered || state.intro < 1) return 0;
      return 1 - THREE.MathUtils.smoothstep(screenDistance(state), 0.1, 0.45);
    },
    // ввод с клавиш на столе: в поле с курсором, иначе в блокнот
    type(key) {
      let el = document.activeElement;
      if (!(el && root.contains(el) && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT'))) { el = launch('note').querySelector('textarea'); el.focus({ preventScroll: true }); }
      const a = el.selectionStart ?? el.value.length, b = el.selectionEnd ?? a;
      if (key === 'Backspace') { if (a === b && a > 0) el.setRangeText('', a - 1, a, 'end'); else el.setRangeText('', a, b, 'end'); } else if (key === 'Enter' && el.tagName === 'INPUT') el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
      else el.setRangeText(key === 'Enter' ? '\n' : key, a, b, 'end');
    },
    reset() { for (const id of [...open.keys()]) close(id); menu.classList.remove('show'); },
    update(state, monitorPower) {
      const d = screenDistance(state);
      // В каждый момент значки рисует либо текстура, либо HTML.
      const vis = state.powered && state.intro >= 1 && state.t - S.onSince >= 5.8 && d < (shown ? 0.26 : 0.16);
      const interactive = vis && state.shutdownAt === null;
      api.busy = interactive && api.site && open.has('horizon');
      hooks.setBare(Number(vis));
      if (vis !== shown) { shown = vis; root.style.display = vis ? 'block' : 'none'; }
      if (!vis) { if (d > 1.5 && open.size) api.reset(); return; }
      tick();
      mesh.updateWorldMatrix(true, false);
      const w = window.innerWidth, h = window.innerHeight;
      const t = homography(quad.map((c) => { v.copy(c).applyMatrix4(mesh.matrixWorld).project(S.camera); return [(v.x * 0.5 + 0.5) * w, (-v.y * 0.5 + 0.5) * h]; }));
      if (t !== lastT) { lastT = t; root.style.transform = t; }
      dk.style.opacity = monitorPower === 1 ? '' : monitorPower.toFixed(3);
      root.inert = !interactive;
      root.style.pointerEvents = interactive ? 'auto' : 'none';
    },
  };
  return api;
}
