// Живые экраны: дисплей на водоблоке, рабочий стол на мониторе, индикатор POST-кодов.
// Большие текстуры монитора заливаются в видеопамять один раз; искры, загрузку, оттенок обоев
// и часы считает шейдер — покадровой перезаливки нет.
import * as THREE from 'three';

const FONT = '"Onest Variable", "Segoe UI", system-ui, sans-serif';
const DISPLAY = '"Unbounded Variable", Bahnschrift, sans-serif';
const MONO = '"JetBrains Mono Variable", Consolas, monospace';
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const hhmm = (d) => String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');

export const WALLPAPERS = [{ name: 'Пепел', hue: 0 }, { name: 'Полночь', hue: 3.75 }, { name: 'Мох', hue: 1.75 }, { name: 'Аметист', hue: 5.0 }];
export const THEMES = ['Кольцо', 'Полосы', 'Часы'];
// положение значков и панели задач в координатах экрана 1920×1080 — их повторяет вёрстка рабочего стола
export const LAYOUT = { icon: { x: 50, y: 44, step: 146, size: 88 }, bar: { x: 520, y: 1002, w: 880, h: 64 }, clock: { x: 1250, y: 1008, w: 132, h: 52 } };

function makeCanvas(w, h, R, mip = true) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.flipY = false;
  tex.anisotropy = Math.min(8, R.capabilities.getMaxAnisotropy());
  tex.generateMipmaps = mip;
  tex.minFilter = mip ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
  return { c, g: c.getContext('2d'), tex };
}
const loadImage = (src) => new Promise((res) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = src; });
function rr(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }

const MONITOR_FRAG = /* glsl */`
  uniform sampler2D uWall; uniform sampler2D uUi; uniform sampler2D uBoot; uniform sampler2D uClock;
  uniform vec4 uClockRect;
  uniform float uTime; uniform float uLogo; uniform float uOn; uniform float uHue; uniform float uBare;
  varying vec2 vUv;
  float h21(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
  vec3 hue(vec3 c, float a){ const vec3 k = vec3(0.57735); float ca = cos(a); return c * ca + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - ca); }
  vec3 embers(vec2 uv, float cells, float speed, float size){
    vec2 p = vec2(uv.x * cells * 1.78, uv.y * cells - uTime * speed);
    vec2 id = floor(p), f = fract(p);
    float r = h21(id);
    vec2 c = vec2(0.2 + 0.6 * h21(id + 7.1), 0.2 + 0.6 * h21(id + 3.7));
    c.x += 0.12 * sin(uTime * (0.4 + r) + r * 40.0);
    float tw = 0.55 + 0.45 * sin(uTime * (1.5 + 2.0 * r) + r * 30.0);
    float a = smoothstep(size * (0.5 + r), 0.0, length(f - c)) * tw * step(0.5, r);
    return mix(vec3(0.62, 0.62, 0.68), vec3(1.0, 0.45, 0.22), step(0.72, r)) * a;
  }
  void main(){
    vec2 uv = vec2(vUv.x, 1.0 - vUv.y);
    vec3 col = texture2D(uWall, vUv).rgb;
    col += embers(uv, 11.0, 0.2, 0.04) * 0.7 + embers(uv + 3.3, 23.0, 0.3, 0.05) * 0.45;
    col = max(hue(col, uHue), 0.0);
    vec4 ui = texture2D(uUi, vUv);
    vec2 cu = (vUv - uClockRect.xy) / uClockRect.zw;
    if (cu.x > 0.0 && cu.x < 1.0 && cu.y > 0.0 && cu.y < 1.0) ui.rgb = texture2D(uClock, cu).rgb;
    col = mix(col, ui.rgb, ui.a * (1.0 - uBare));
    gl_FragColor = vec4(mix(texture2D(uBoot, vUv).rgb * uLogo, col, uOn), 1.0);
  }`;

export async function createScreens(S) {
  const R = S.renderer;
  const pump = makeCanvas(512, 512, R);
  const dbg = makeCanvas(160, 96, R, false);
  const wall = makeCanvas(1920, 1080, R);
  const ui = makeCanvas(1920, 1080, R);
  const boot = makeCanvas(640, 360, R, false);
  const clock = makeCanvas(264, 104, R, false);
  S.screens.screen_pump.material = new THREE.MeshBasicMaterial({ map: pump.tex, toneMapped: false });
  S.screens.screen_debug.material = new THREE.MeshBasicMaterial({ map: dbg.tex, toneMapped: false });
  const L = LAYOUT;
  const U = {
    uWall: { value: wall.tex }, uUi: { value: ui.tex }, uBoot: { value: boot.tex }, uClock: { value: clock.tex },
    uClockRect: { value: new THREE.Vector4(L.clock.x / 1920, L.clock.y / 1080, L.clock.w / 1920, L.clock.h / 1080) },
    uTime: { value: 0 }, uLogo: { value: 0 }, uOn: { value: 0 }, uHue: { value: 0 }, uBare: { value: 0 },
  };
  S.screens.screen_monitor.material = new THREE.ShaderMaterial({
    uniforms: U, fragmentShader: MONITOR_FRAG,
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  });
  const [icV, icC, icH] = await Promise.all(['vivid', 'coolerscreen', 'horizon'].map((n) => loadImage(`/icons/${n}.png`)));
  let bootAt = null, acc = 0, lastKey = '', lastMinute = -1, theme = 0, accent = '#ff6b4a', hueTarget = 0, dbgCode = null;

  // ----- экран загрузки
  {
    const g = boot.g;
    g.fillStyle = '#000'; g.fillRect(0, 0, 640, 360);
    g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = '#eef0f4';
    g.font = `600 22px ${DISPLAY}`; g.fillText('С Б О Р К А', 320, 168);
    g.fillStyle = accent; g.fillRect(296, 198, 48, 2);
  }

  // ----- обои
  {
    const g = wall.g;
    const sky = g.createLinearGradient(0, 0, 0, 1080);
    sky.addColorStop(0, '#05070d'); sky.addColorStop(0.55, '#11131c'); sky.addColorStop(0.8, '#2a1a1c'); sky.addColorStop(1, '#3a1d18');
    g.fillStyle = sky; g.fillRect(0, 0, 1920, 1080);
    let seed = 11;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(210,220,255,${0.15 + rnd() * 0.5})`; g.fillRect(rnd() * 1920, rnd() * 620, 1 + rnd() * 1.6, 1 + rnd() * 1.6); }
    const glow = g.createRadialGradient(1280, 900, 20, 1280, 900, 720);
    glow.addColorStop(0, 'rgba(255,110,60,0.5)'); glow.addColorStop(0.4, 'rgba(200,70,40,0.16)'); glow.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = glow; g.fillRect(0, 0, 1920, 1080);
    const ridge = (base, amp, col, s) => {
      seed = s; g.fillStyle = col; g.beginPath(); g.moveTo(0, 1080);
      let y = base;
      for (let x = 0; x <= 1920; x += 16) { y += (rnd() - 0.5) * amp; y += (base - y) * 0.06; g.lineTo(x, y + Math.sin(x * 0.004 + s) * amp * 1.6); }
      g.lineTo(1920, 1080); g.fill();
    };
    ridge(720, 26, '#191319', 3); ridge(800, 34, '#120e12', 9); ridge(900, 40, '#0a080a', 21); ridge(1000, 30, '#050405', 5);
  }

  // ----- слой интерфейса: значки и панель задач на прозрачном фоне
  function folder(g, x, y, s) {
    g.fillStyle = '#c88a3e'; rr(g, x + s * 0.1, y + s * 0.2, s * 0.36, s * 0.16, s * 0.05); g.fill();
    g.fillStyle = '#e9a54d'; rr(g, x + s * 0.1, y + s * 0.28, s * 0.8, s * 0.54, s * 0.07); g.fill();
    g.fillStyle = '#f5bd6a'; rr(g, x + s * 0.1, y + s * 0.38, s * 0.8, s * 0.44, s * 0.07); g.fill();
  }
  function note(g, x, y, s) {
    g.fillStyle = '#e8ebf2'; rr(g, x + s * 0.2, y + s * 0.1, s * 0.6, s * 0.8, s * 0.07); g.fill();
    g.fillStyle = '#9aa0ac';
    for (let i = 0; i < 4; i++) g.fillRect(x + s * 0.3, y + s * (0.3 + i * 0.13), s * (i === 3 ? 0.24 : 0.4), s * 0.045);
  }
  {
    const g = ui.g;
    g.clearRect(0, 0, 1920, 1080);
    g.textAlign = 'center'; g.textBaseline = 'alphabetic'; g.font = `500 21px ${FONT}`;
    [['Vivid', icV], ['CoolerScreen', icC], ['Horizon', icH], ['Проекты', 'folder'], ['обо мне.txt', 'note']].forEach(([name, img], i) => {
      const x = L.icon.x, y = L.icon.y + i * L.icon.step, s = L.icon.size;
      if (img === 'folder') folder(g, x, y, s); else if (img === 'note') note(g, x, y, s); else if (img) g.drawImage(img, x, y, s, s);
      g.fillStyle = 'rgba(0,0,0,0.7)'; g.fillText(name, x + s / 2 + 1, y + s + 31);
      g.fillStyle = '#f2f4f8'; g.fillText(name, x + s / 2, y + s + 30);
    });
    const b = L.bar;
    g.fillStyle = 'rgba(12,13,17,0.92)'; rr(g, b.x, b.y, b.w, b.h, 20); g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.07)'; g.lineWidth = 1.5; rr(g, b.x, b.y, b.w, b.h, 20); g.stroke();
    g.fillStyle = '#e8ebf2';
    for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(560 + (i % 2) * 13, 1027.5 + (i >> 1) * 13, 4.2, 0, 7); g.fill(); }
    g.fillStyle = 'rgba(255,255,255,0.06)'; rr(g, 600, 1014, 190, 40, 20); g.fill();
    g.strokeStyle = '#8b919c'; g.lineWidth = 2.4; g.beginPath(); g.arc(626, 1033, 7, 0, 7); g.stroke();
    g.beginPath(); g.moveTo(631.5, 1038.5); g.lineTo(636, 1043); g.stroke();
    g.textAlign = 'left'; g.fillStyle = '#8b919c'; g.font = `500 18px ${FONT}`; g.fillText('Поиск', 648, 1040);
    [icV, icC, icH].forEach((img, i) => { if (img) g.drawImage(img, 830 + i * 62, 1011, 46, 46); });
    folder(g, 830 + 3 * 62, 1011, 46); note(g, 830 + 4 * 62, 1011, 46);
    g.strokeStyle = '#cfd3dc'; g.lineWidth = 2.2; g.lineCap = 'round';
    for (let i = 0; i < 3; i++) { g.beginPath(); g.arc(1190, 1042, 5 + i * 5.5, -Math.PI * 0.75, -Math.PI * 0.25); g.stroke(); }
    g.fillStyle = '#cfd3dc'; g.beginPath(); g.arc(1190, 1042, 2.2, 0, 7); g.fill();
    g.beginPath(); g.moveTo(1216, 1029); g.lineTo(1222, 1029); g.lineTo(1229, 1023); g.lineTo(1229, 1045); g.lineTo(1222, 1039); g.lineTo(1216, 1039); g.closePath(); g.fill();
  }
  function drawClock() {
    const g = clock.g, d = new Date();
    g.fillStyle = '#0c0d11'; g.fillRect(0, 0, 264, 104);
    g.textAlign = 'right'; g.textBaseline = 'alphabetic';
    g.fillStyle = '#eef0f4'; g.font = `500 38px ${MONO}`; g.fillText(hhmm(d), 252, 46);
    g.fillStyle = '#9aa0ac'; g.font = `500 28px ${MONO}`;
    g.fillText(d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' }), 252, 88);
    clock.tex.needsUpdate = true;
  }
  drawClock();

  // ----- дисплей водоблока: три темы в духе CoolerScreen
  const sens = { cpu: 30, gpu: 30, rpm: 0 };
  function drawPump(since) {
    const g = pump.g, cx = 256, cy = 256;
    g.fillStyle = '#000'; g.fillRect(0, 0, 512, 512);
    if (since < 1.0) return;
    g.textAlign = 'center'; g.textBaseline = 'alphabetic';
    if (since < 3.0) {
      g.globalAlpha = smooth(1.0, 1.6, since) * (1 - smooth(2.5, 3.0, since));
      if (icC) g.drawImage(icC, cx - 60, cy - 108, 120, 120);
      g.fillStyle = '#f2f4f8'; g.font = `600 34px ${DISPLAY}`; g.fillText('CoolerScreen', cx, cy + 64);
      g.fillStyle = accent; g.fillRect(cx - 30, cy + 92, 60 * smooth(1.2, 2.4, since), 4);
      g.globalAlpha = 1;
      return;
    }
    const k = smooth(3.0, 4.4, since);
    const cpu = Math.round(sens.cpu * k), gpu = Math.round(sens.gpu * k), rpm = Math.round(sens.rpm * k / 20) * 20;
    g.fillStyle = '#0b0c0f'; g.beginPath(); g.arc(cx, cy, 250, 0, 7); g.fill();
    if (theme === 1) {          // полосы
      [['ПРОЦЕССОР', cpu + '°', (cpu - 20) / 70], ['ВИДЕО', gpu + '°', (gpu - 20) / 70], ['ПОМПА', String(rpm), rpm / 3200]].forEach(([n, v, f], i) => {
        const y = 150 + i * 92;
        g.textAlign = 'left'; g.fillStyle = '#8b919c'; g.font = `500 22px ${MONO}`; g.fillText(n, 96, y);
        g.textAlign = 'right'; g.fillStyle = '#f4f6fa'; g.font = `600 34px ${DISPLAY}`; g.fillText(v, 416, y + 4);
        g.fillStyle = '#1d2026'; rr(g, 96, y + 18, 320, 12, 6); g.fill();
        g.fillStyle = accent; rr(g, 96, y + 18, Math.max(12, 320 * clamp(f)), 12, 6); g.fill();
      });
      return;
    }
    if (theme === 2) {          // часы
      const d = new Date();
      g.fillStyle = '#f4f6fa'; g.font = `600 104px ${DISPLAY}`; g.fillText(hhmm(d), cx, cy + 22);
      g.fillStyle = '#8b919c'; g.font = `500 24px ${MONO}`;
      g.fillText(d.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' }).toUpperCase(), cx, cy - 96);
      g.fillStyle = accent; g.font = `600 40px ${DISPLAY}`; g.fillText(cpu + '°', cx - 70, cy + 120);
      g.fillStyle = '#e6e9ee'; g.fillText(gpu + '°', cx + 70, cy + 120);
      g.fillStyle = '#8b919c'; g.font = `500 20px ${MONO}`; g.fillText('ЦП', cx - 70, cy + 152); g.fillText('ВИДЕО', cx + 70, cy + 152);
      return;
    }
    const a0 = Math.PI * 0.75, a1 = Math.PI * 2.25;
    g.lineCap = 'round'; g.strokeStyle = '#1d2026'; g.lineWidth = 22;
    g.beginPath(); g.arc(cx, cy, 206, a0, a1); g.stroke();
    g.strokeStyle = accent;
    g.beginPath(); g.arc(cx, cy, 206, a0, a0 + (a1 - a0) * clamp((Math.round(sens.cpu) - 20) / 70) * k); g.stroke();
    g.strokeStyle = '#3a3e47'; g.lineWidth = 3; g.lineCap = 'butt';
    for (let i = 0; i <= 28; i++) {
      const a = a0 + (a1 - a0) * i / 28, r0 = i % 7 === 0 ? 166 : 174;
      g.beginPath(); g.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); g.lineTo(cx + Math.cos(a) * 182, cy + Math.sin(a) * 182); g.stroke();
    }
    g.fillStyle = '#8b919c'; g.font = `500 25px ${MONO}`; g.fillText('ПРОЦЕССОР', cx, cy - 76);
    g.fillStyle = '#f4f6fa'; g.font = `600 124px ${DISPLAY}`;
    const s = String(cpu), wnum = g.measureText(s).width;
    g.fillText(s, cx - 18, cy + 46);
    g.font = `500 44px ${FONT}`; g.fillStyle = accent; g.fillText('°C', cx - 18 + wnum / 2 + 36, cy - 8);
    g.font = `500 23px ${MONO}`; g.fillStyle = '#8b919c';
    g.fillText('ВИДЕО', cx - 78, cy + 110); g.fillText('ПОМПА', cx + 78, cy + 110);
    g.fillStyle = '#e6e9ee'; g.font = `600 34px ${DISPLAY}`;
    g.fillText(gpu + '°', cx - 78, cy + 156); g.fillText(String(rpm), cx + 78, cy + 156);
    g.fillStyle = '#6d727c'; g.font = `500 25px ${MONO}`; g.fillText(hhmm(new Date()), cx, cy + 212);
  }

  // ----- индикатор кодов
  const SEG = { 0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 9: 'abfgcd', A: 'abcefg', b: 'cdefg', d: 'bcdeg', F: 'aefg' };
  const CODES = ['00', '15', '19', '2b', '32', '4F', '55', '62', '99', 'Ad', 'b2', 'A0'];
  function digit(g, ch, x, y, w, h) {
    const on = SEG[ch] || '', t = 9;
    const seg = { a: [x + t, y, w - 2 * t, t], d: [x + t, y + h - t, w - 2 * t, t], g: [x + t, y + h / 2 - t / 2, w - 2 * t, t],
      f: [x, y + t, t, h / 2 - t * 1.5], b: [x + w - t, y + t, t, h / 2 - t * 1.5], e: [x, y + h / 2 + t / 2, t, h / 2 - t * 1.5], c: [x + w - t, y + h / 2 + t / 2, t, h / 2 - t * 1.5] };
    for (const k in seg) { g.fillStyle = on.includes(k) ? accent : '#1c0a06'; g.fillRect(...seg[k]); }
  }
  function drawDebug(code) {
    const g = dbg.g;
    g.fillStyle = '#050101'; g.fillRect(0, 0, 160, 96);
    if (code) { digit(g, code[0], 22, 12, 50, 72); digit(g, code[1], 88, 12, 50, 72); }
    dbg.tex.needsUpdate = true;
  }
  drawPump(-1); drawDebug('');
  // все текстуры уходят в видеопамять заранее, под заставкой
  for (const t of [pump.tex, dbg.tex, wall.tex, ui.tex, boot.tex, clock.tex]) { t.needsUpdate = true; R.initTexture(t); }

  return {
    get theme() { return theme; },
    get wallpaper() { return WALLPAPERS.findIndex((w) => w.hue === hueTarget); },
    boot(t) { bootAt = t; lastKey = ''; },
    setTheme(i) { theme = i; lastKey = ''; },
    setAccent(css) { accent = css; lastKey = ''; dbgCode = null; },
    setWallpaper(i) { hueTarget = WALLPAPERS[i].hue; },
    setBare(v) { U.uBare.value = v; },
    update(dt, t, monitorPower, casePower) {
      const since = bootAt == null ? -1 : t - bootAt;
      const on = since > 0 ? 1 : 0;
      sens.cpu += ((43 + 5 * Math.sin(t * 0.21) + 2 * Math.sin(t * 1.3)) * on + 30 * (1 - on) - sens.cpu) * Math.min(1, dt * 0.9);
      sens.gpu += ((47 + 6 * Math.sin(t * 0.17 + 2)) * on + 30 * (1 - on) - sens.gpu) * Math.min(1, dt * 0.7);
      sens.rpm += ((2380 + 60 * Math.sin(t * 0.5)) * on - sens.rpm) * Math.min(1, dt * 0.8);
      U.uTime.value = t;
      U.uLogo.value = smooth(2.8, 3.4, since) * (1 - smooth(4.5, 5.0, since)) * monitorPower;
      U.uOn.value = smooth(5.0, 5.8, since) * monitorPower;
      S.screens.screen_pump.material.color.setScalar(casePower);
      S.screens.screen_debug.material.color.setScalar(casePower);
      // оттенок обоев меняется плавно, кратчайшей дугой
      let dh = hueTarget - U.uHue.value;
      dh -= Math.round(dh / 6.2832) * 6.2832;
      U.uHue.value += dh * Math.min(1, dt * 3);
      const minute = new Date().getMinutes();
      if (minute !== lastMinute) { lastMinute = minute; drawClock(); }
      acc += dt;
      if (acc < 1 / 20) return;
      acc = 0;
      const anim = since >= 0 && since < 4.6;
      const key = anim ? 'a' + t : [Math.round(sens.cpu), Math.round(sens.gpu), Math.round(sens.rpm / 20), minute, since < 0, theme].join();
      if (key !== lastKey) { lastKey = key; drawPump(since); pump.tex.needsUpdate = true; }
      const code = since < 0.3 ? '' : CODES[Math.min(CODES.length - 1, Math.floor((since - 0.3) / 0.33))];
      if (code !== dbgCode) { dbgCode = code; drawDebug(code); }
    },
  };
}
