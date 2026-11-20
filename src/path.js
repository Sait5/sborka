// Путь камеры: ключевые кадры в миллиметрах сцены (как в Blender), интерполяция по прокрутке.
import * as THREE from 'three';
import { B } from './scene.js';

// кадр «до включения» — кнопка питания крупно
export const OFF = { pos: [318, -212, 596], tgt: [217, -90, 510], fov: 27 };

// остановки по прокрутке; id совпадает с блоком текста на странице
export const STOPS = [
  { id: 'hero', pos: [640, -660, 430], tgt: [5, -5, 285], fov: 31, shift: -5.5 },
  { id: 'velocity', pos: [70, -540, 300], tgt: [-60, -95, 188], fov: 30, shift: -4 },
  { id: 'resonance', pos: [80, -230, 470], tgt: [-28, 14, 372], fov: 30, shift: 4 },
  { id: 'cooler', pos: [-190, -310, 398], tgt: [-112, 28, 372], fov: 28, shift: 4.5 },
  { id: 'vivid', pos: [405, -305, 322], tgt: [193, -20, 286], fov: 34, shift: -4.5 },
  { id: 'horizon', pos: [150, -430, 500], tgt: [-115, 40, 335], fov: 30, shift: 4.5 },
  { id: 'out', pos: [560, -560, 420], tgt: [-60, -330, 300], fov: 34, shift: 0 },
  { id: 'monitor', pos: [606, -620, 365], tgt: [-194.6, -620, 309], fov: 30, shift: 0 },
  { id: 'desk', pos: [900, -560, 590], tgt: [-120, -590, 120], fov: 44, shift: 0 },
  { id: 'final', pos: [1650, -40, 640], tgt: [-120, -400, 235], fov: 38, shift: -4.5 },
];

const P = STOPS.map((s) => B(...s.pos));
const T = STOPS.map((s) => B(...s.tgt));
const posCurve = new THREE.CatmullRomCurve3(P, false, 'centripetal', 0.5);
const tgtCurve = new THREE.CatmullRomCurve3(T, false, 'centripetal', 0.5);
const N = STOPS.length - 1;

const ease = (x) => x * x * (3 - 2 * x);

// p ∈ [0, 1] → положение камеры. Между остановками движение замедляется у самих остановок.
export function sample(p, out) {
  const f = Math.min(N - 1e-6, Math.max(0, p * N));
  const i = Math.floor(f);
  const x = f - i;
  const a = STOPS[i], b = STOPS[i + 1];
  // Промежуточный ракурс между корпусом и монитором проходим без остановки.
  let progress = ease(x);
  if (b.id === 'out') progress = x * x * (2 - x);
  if (a.id === 'out') progress = x * (1 + x * (1 - x));
  const u = (i + progress) / N;
  // у CatmullRomCurve3 параметр t равномерен по точкам
  posCurve.getPoint(u, out.pos);
  tgtCurve.getPoint(u, out.tgt);
  out.fov = a.fov + (b.fov - a.fov) * progress;
  out.shift = a.shift + (b.shift - a.shift) * progress;
  out.index = i;
  out.local = f - i;
  return out;
}

export const stopAt = (i) => i / N;
export const offPose = { pos: B(...OFF.pos), tgt: B(...OFF.tgt), fov: OFF.fov };
