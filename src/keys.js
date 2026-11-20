// Клавиатура и мышь на столе: клавиши нажимаются — и от настоящей клавиатуры, и по щелчку в сцене;
// мышь на коврике повторяет движения курсора.
// Все колпачки — один меш; у каждой вершины записан номер её клавиши, а глубину нажатия
// шейдер берёт из крошечной текстуры. Так нажатия не добавляют ни одного вызова отрисовки.
import * as THREE from 'three';

const U = 19.05, X0 = -18.25 * U / 2, Y0 = 6.4 * U / 2;
const ROW_Y = [0, 1.4, 2.4, 3.4, 4.4, 5.4];
const SYM = { '`': 'Backquote', '-': 'Minus', '=': 'Equal', '[': 'BracketLeft', ']': 'BracketRight', ';': 'Semicolon', "'": 'Quote', ',': 'Comma', '.': 'Period', '/': 'Slash' };
const codeOf = (c) => SYM[c] || (c >= '0' && c <= '9' ? 'Digit' + c : 'Key' + c.toUpperCase());
const line = (lat, ru, at) => [...lat].map((c, i) => [codeOf(c), 1, at + i, ru[i]]);
const ROWS = [
  [['Escape', 1, 0], ...[0, 1, 2, 3].map((i) => ['F' + (i + 1), 1, 2 + i]), ...[0, 1, 2, 3].map((i) => ['F' + (i + 5), 1, 6.5 + i]),
    ...[0, 1, 2, 3].map((i) => ['F' + (i + 9), 1, 11 + i]), ['PrintScreen', 1, 15.25], ['ScrollLock', 1, 16.25], ['Pause', 1, 17.25]],
  [...line('`1234567890-=', 'ё1234567890-=', 0), ['Backspace', 2, 13, 'Backspace'], ['Insert', 1, 15.25], ['Home', 1, 16.25], ['PageUp', 1, 17.25]],
  [['Tab', 1.5, 0], ...line('qwertyuiop[]', 'йцукенгшщзхъ', 1.5), ['Backslash', 1.5, 13.5, '\\'], ['Delete', 1, 15.25], ['End', 1, 16.25], ['PageDown', 1, 17.25]],
  [['CapsLock', 1.75, 0], ...line("asdfghjkl;'", 'фывапролджэ', 1.75), ['Enter', 2.25, 12.75, 'Enter']],
  [['ShiftLeft', 2.25, 0], ...line('zxcvbnm,./', 'ячсмитьбю.', 2.25), ['ShiftRight', 2.75, 12.25], ['ArrowUp', 1, 16.25]],
  [['ControlLeft', 1.25, 0], ['MetaLeft', 1.25, 1.25], ['AltLeft', 1.25, 2.5], ['Space', 6.25, 3.75, ' '], ['AltRight', 1.25, 10], ['Fn', 1.25, 11.25],
    ['ContextMenu', 1.25, 12.5], ['ControlRight', 1.25, 13.75], ['ArrowLeft', 1, 15.25], ['ArrowDown', 1, 16.25], ['ArrowRight', 1, 17.25]],
];

export function createKeys(S) {
  const keys = [];
  ROWS.forEach((row, r) => row.forEach(([code, w, cx, ch]) => keys.push({ code, ch, r, x: X0 + (cx + w / 2) * U, y: Y0 - (ROW_Y[r] + 0.5) * U, hw: w * U / 2 })));
  const byCode = new Map(keys.map((k, i) => [k.code, i]));
  // клавиша по точке в местных координатах клавиатуры (метры, Y вверх)
  const keyAt = (X, Z) => {
    const bx = X * 1000, by = -Z * 1000;
    for (let i = 0; i < keys.length; i++) { const k = keys[i]; if (Math.abs(by - k.y) <= U / 2 + 0.2 && Math.abs(bx - k.x) <= k.hw + 0.2) return i; }
    return -1;
  };

  const data = new Uint8Array(128);
  const tex = new THREE.DataTexture(data, 128, 1, THREE.RedFormat);
  tex.minFilter = tex.magFilter = THREE.NearestFilter;
  tex.needsUpdate = true;
  const uKeys = { value: tex };
  const caps = [];
  const kb = S.nodes.keyboard;
  if (kb) kb.traverse((o) => {
    if (!o.isMesh || !/keycap|legend/i.test(o.name)) return;
    const p = o.geometry.attributes.position, a = new Float32Array(p.count);
    for (let i = 0; i < p.count; i++) a[i] = keyAt(p.getX(i), p.getZ(i));
    o.geometry.setAttribute('aKey', new THREE.BufferAttribute(a, 1));
    const m = o.material;
    m.onBeforeCompile = (sh) => {
      sh.uniforms.uKeys = uKeys;
      sh.vertexShader = 'attribute float aKey;\nuniform sampler2D uKeys;\n' + sh.vertexShader.replace('#include <begin_vertex>',
        '#include <begin_vertex>\n  transformed.y -= step(0.0, aKey) * texture2D(uKeys, vec2((max(aKey, 0.0) + 0.5) / 128.0, 0.5)).r * 0.0027;');
    };
    m.customProgramCacheKey = () => 'keys';
    m.needsUpdate = true;
    if (/keycap/i.test(o.name)) caps.push(o);
  });

  const held = new Uint8Array(keys.length), tap = new Float32Array(keys.length), val = new Float32Array(keys.length);
  const mouse = S.nodes.mouse, base = mouse ? mouse.position.clone() : null;
  let dip = 0, mx = 0, my = 0;
  const local = new THREE.Vector3();

  return {
    keys,
    // настоящая клавиатура
    set(code, down) { const i = byCode.get(code); if (i != null) held[i] = down ? 1 : 0; },
    release() { held.fill(0); },
    // щелчок по клавише в сцене: возвращает клавишу или null
    pick(ray) {
      const hit = ray.intersectObjects(caps, false)[0];
      if (!hit) return null;
      hit.object.worldToLocal(local.copy(hit.point));
      const i = keyAt(local.x, local.z);
      if (i < 0) return null;
      tap[i] = 0.13;
      return keys[i];
    },
    hitsMouse(ray) { return mouse ? ray.intersectObject(mouse, true).length > 0 : false; },
    click() { dip = 1; },
    update(dt, px, py, amount) {
      let dirty = false;
      for (let i = 0; i < keys.length; i++) {
        if (tap[i] > 0) tap[i] -= dt;
        const target = held[i] || tap[i] > 0 ? 1 : 0;
        if (val[i] === target) continue;
        val[i] += (target - val[i]) * Math.min(1, dt * 42);
        if (Math.abs(val[i] - target) < 0.02) val[i] = target;
        data[i] = Math.round(val[i] * 255);
        dirty = true;
      }
      if (dirty) tex.needsUpdate = true;
      if (!mouse) return;
      // мышь едет по коврику вслед за курсором и чуть «проседает» при щелчке
      const k = Math.min(1, dt * 9);
      mx += (px * amount - mx) * k;
      my += (py * amount - my) * k;
      dip = Math.max(0, dip - dt * 9);
      mouse.position.set(base.x + mx * 0.05, base.y - Math.sin(dip * Math.PI) * 0.0009, base.z - my * 0.032);
    },
  };
}
