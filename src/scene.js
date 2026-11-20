// Сцена: рендерер, окружение, загрузка модели, материалы, свет, постобработка.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';

// миллиметры Blender (Z вверх) → метры three (Y вверх)
export const B = (x, y, z) => new THREE.Vector3(x, z, -y).multiplyScalar(0.001);

export const ACCENT = new THREE.Color().setRGB(1.0, 0.2, 0.07);
export const WHITE = new THREE.Color().setRGB(0.78, 0.86, 1.0);
export const WARM = new THREE.Color().setRGB(1.0, 0.9, 0.76);

const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

export function createScene(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.shadowMap.autoUpdate = false;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  RectAreaLightUniformsLib.init();
  canvas.addEventListener('webglcontextlost', (e) => e.preventDefault());
  canvas.addEventListener('webglcontextrestored', () => location.reload());

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x020203);
  const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 40);

  // --- окружение для отражений: тёмная комната с окном и парой мягких панелей
  const envScene = new THREE.Scene();
  const ebox = (w, h, d, x, y, z, col, k) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), new THREE.MeshBasicMaterial({ color: new THREE.Color(col).multiplyScalar(k) }));
    m.position.set(x, y, z);
    envScene.add(m);
  };
  ebox(7, 0.1, 5, 0, 4.2, 0, 0x8fa2c8, 0.5);
  ebox(0.1, 2.6, 1.6, 6, 1.6, 2.5, 0xa9c4ff, 2.6);
  ebox(0.1, 2.6, 1.6, 6, 1.6, -0.5, 0xa9c4ff, 1.6);
  ebox(2.4, 1.4, 0.1, -1, 1.2, 6, 0xffc4a0, 1.6);
  ebox(0.1, 1.0, 3.0, -6, 0.8, 0, 0x7f8aa0, 1.0);
  ebox(9, 0.1, 9, 0, -2.5, 0, 0x202228, 0.6);
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(envScene, 0.035).texture;
  scene.environmentIntensity = 0.55;

  // --- постобработка
  const target = new THREE.WebGLRenderTarget(4, 4, { type: THREE.HalfFloatType, samples: 4 });
  const composer = new EffectComposer(renderer, target);
  composer.addPass(new RenderPass(scene, camera));
  const gtao = new GTAOPass(scene, camera, 4, 4);
  gtao.updateGtaoMaterial({ radius: 0.035, distanceExponent: 1.4, thickness: 1.2, scale: 1.25, samples: 12, distanceFallOff: 1, screenSpaceRadius: false });
  gtao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, radiusExponent: 1, rings: 2, samples: 12 });
  const noAO = [];
  const gtaoRender = gtao.render.bind(gtao);
  gtao.render = (...a) => {
    for (const o of noAO) o.visible = false;
    gtaoRender(...a);
    for (const o of noAO) o.visible = true;
  };
  composer.addPass(gtao);
  const bloom = new UnrealBloomPass(new THREE.Vector2(4, 4), 0.34, 0.62, 1.0);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  const S = {
    renderer, scene, camera, composer, gtao, bloom, noAO,
    leds: [], rotors: [], lights: [], screens: {}, nodes: {}, coolant: null, time: 0,
    accent: { emissive: [], lights: [], paint: [] },
    frames: 0, shadowDone: false,
    power: 1,        // доля мощности при затухании
    onSince: null,
  };

  S.resize = () => {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    renderer.setSize(w, h, false);
    composer.setSize(w, h);
    // затенение считается в половинном разрешении: на глаз то же, а стоит вчетверо меньше
    const pr = renderer.getPixelRatio();
    gtao.setSize(Math.round(w * pr / 2), Math.round(h * pr / 2));
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };

  S.load = (url, onProgress) => new Promise((resolve, reject) => {
    const draco = new DRACOLoader().setDecoderPath('/draco/');
    new GLTFLoader().setDRACOLoader(draco).load(url, (gltf) => {
      setup(S, gltf.scene);
      resolve(S);
    }, onProgress, reject);
  });

  S.warm = () => {
    const off = [];
    scene.traverse((o) => { if (o.isMesh && o.frustumCulled) { o.frustumCulled = false; off.push(o); } });
    renderer.shadowMap.needsUpdate = true;
    S.shadowDone = true;
    composer.render();
    composer.render();
    for (const o of off) o.frustumCulled = true;
  };
  // цвет подсветки: диоды, свет, жидкость и цветные детали оплётки
  S.setAccent = (css) => {
    const c = new THREE.Color(css);
    for (const m of S.accent.emissive) m.emissive.copy(c);
    for (const l of S.accent.lights) l.color.copy(c);
    for (const m of S.accent.paint) m.color.copy(c).multiplyScalar(0.72);
    if (S.coolant) { S.coolant.emissive.copy(c); S.coolant.userData.u.uTint.value.copy(c); }
    if (S.bubbles) S.bubbles.mat.color.copy(c).lerp(new THREE.Color(1, 1, 1), 0.35);
  };
  S.update = (dt, t) => update(S, dt, t);
  S.render = () => composer.render();
  return S;
}

// ---------- материалы

function glassMaterial(rough = 0.03, env = 1.0, spec = 1.0) {
  return new THREE.MeshPhysicalMaterial({
    color: 0x000000, roughness: rough, metalness: 0, envMapIntensity: env, specularIntensity: spec,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
  });
}

const NOISE = /* glsl */`
  float h13(vec3 p){ p = fract(p * 0.1031); p += dot(p, p.zyx + 31.32); return fract((p.x + p.y) * p.z); }
  float vnoise(vec3 p){ vec3 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
    return mix(mix(mix(h13(i), h13(i+vec3(1,0,0)), f.x), mix(h13(i+vec3(0,1,0)), h13(i+vec3(1,1,0)), f.x), f.y),
               mix(mix(h13(i+vec3(0,0,1)), h13(i+vec3(1,0,1)), f.x), mix(h13(i+vec3(0,1,1)), h13(i+vec3(1,1,1)), f.x), f.y), f.z); }
`;

function coolantMaterial(S) {
  const m = new THREE.MeshStandardMaterial({ color: 0x180503, roughness: 0.25, metalness: 0.0, emissive: ACCENT.clone(), emissiveIntensity: 1 });
  m.userData.u = { uTime: { value: 0 }, uGlow: { value: 0 }, uTint: { value: ACCENT.clone() } };
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = m.userData.u.uTime;
    sh.uniforms.uGlow = m.userData.u.uGlow;
    sh.uniforms.uTint = m.userData.u.uTint;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWp;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvWp = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vWp;\nuniform float uTime;\nuniform float uGlow;\nuniform vec3 uTint;\n' + NOISE)
      .replace('#include <emissivemap_fragment>', /* glsl */`#include <emissivemap_fragment>
        float n1 = vnoise(vWp * 55.0 + vec3(0.0, -uTime * 0.55, uTime * 0.2));
        float n2 = vnoise(vWp * 140.0 + vec3(uTime * 0.3, -uTime * 0.9, 0.0));
        float fres = pow(1.0 - abs(dot(normalize(vNormal), normalize(vViewPosition))), 1.6);
        float body = 0.42 + 0.5 * n1 + 0.22 * n2;
        totalEmissiveRadiance *= uGlow * body * (0.55 + 0.75 * (1.0 - fres));
        diffuseColor.rgb = mix(uTint * 0.045, uTint * 0.3, clamp(uGlow, 0.0, 1.0));`);
  };
  return m;
}

function setup(S, root) {
  const { scene } = S;
  scene.add(root);
  const cache = new Map();
  const ledDefs = {
    led_accent: { color: ACCENT, k: 3.2 }, led_white: { color: WHITE, k: 2.6 }, led_ram: { color: WHITE, k: 2.4 },
    led_gpu: { color: WHITE, k: 2.2 }, led_kbd: { color: WHITE, k: 0.5 }, led_wall: { color: ACCENT, k: 3.0 },
    legend: { color: WHITE, k: 0.9 }, led_bar: { color: WARM, k: 3.2 },
  };
  root.updateMatrixWorld(true);
  const wp = new THREE.Vector3();

  root.traverse((o) => {
    if (o.name) S.nodes[o.name] = o;
    if (/rotor/i.test(o.name) && !o.isMesh) S.rotors.push({ node: o, gpu: /gpu/i.test(o.name), blades: [], angle: Math.random() * 6 });
    if (!o.isMesh) return;
    const name = o.material.name;
    o.frustumCulled = true;
    if (name.startsWith('screen_')) {
      S.screens[name] = o;
      return;
    }
    if (name === 'glass_panel') {
      o.material = cache.get(name) || cache.set(name, glassMaterial(0.06, 1.0, 0.26)).get(name);      // слабый блеск: монитор отражается в стекле, но не закрывает плату
      o.renderOrder = 20;
      S.noAO.push(o);
      // лёгкая тонировка вторым слоем
      const tint = new THREE.Mesh(o.geometry, cache.get('tint') || cache.set('tint', new THREE.MeshBasicMaterial({
        color: 0xa9adb6, transparent: true, blending: THREE.MultiplyBlending, premultipliedAlpha: true, depthWrite: false, side: THREE.FrontSide,
      })).get('tint'));
      tint.renderOrder = 19;
      o.add(tint);
      S.noAO.push(tint);
      return;
    }
    if (name === 'glass_tube' || name === 'acrylic') {
      o.material = cache.get(name) || cache.set(name, glassMaterial(0.02, 1.6)).get(name);
      o.renderOrder = 10;
      S.noAO.push(o);
      return;
    }
    if (name === 'coolant') {
      S.coolant = S.coolant || coolantMaterial(S);
      o.material = S.coolant;
      return;
    }
    if (name === 'led_power') {
      const m = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.4, emissive: WHITE.clone(), emissiveIntensity: 0 });
      o.material = m;
      S.powerLed = S.powerLed || [];
      S.powerLed.push(m);
      return;
    }
    if (ledDefs[name]) {
      const d = ledDefs[name];
      const m = new THREE.MeshStandardMaterial({ color: 0x0a0a0a, roughness: 0.45, emissive: d.color.clone(), emissiveIntensity: 0 });
      o.material = m;
      o.getWorldPosition(wp);
      // волна включения идёт от кнопки питания вглубь корпуса
      const inPc = !/desk|keyboard|mouse|monitor|pad/i.test(pathOf(o));
      const delay = inPc ? 0.25 + wp.distanceTo(B(219, -92, 512)) * 2.6 : 2.2 + Math.random() * 0.3;
      S.leds.push({ m, k: d.k, delay, kind: name });
      if (d.color === ACCENT) S.accent.emissive.push(m);
      return;
    }
    const m = o.material;
    if (m.isMeshStandardMaterial) {
      m.envMapIntensity = 1.0;
      if (name === 'void') { o.material = cache.get('void') || cache.set('void', new THREE.MeshBasicMaterial({ color: 0x000000 })).get('void'); }
      if (name === 'rad_fin') m.side = THREE.DoubleSide;
      if (name === 'chrome') m.roughness = 0.2;
      if (/^(sleeve_accent|print_accent|keycap_accent|stitch)$/.test(name) && !S.accent.paint.includes(m)) S.accent.paint.push(m);
      if (name.startsWith('sleeve') && !m.normalMap) {
        m.normalMap = S.braid || (S.braid = braidTexture());
        S.renderer.initTexture(m.normalMap);
        m.normalScale.set(0.9, 0.9);
        m.roughness = 0.78;
      }
      if (name === 'pcb' && !m.map) {
        m.map = pcbTexture(S.renderer);
        S.renderer.initTexture(m.map);
        m.color.set(0xffffff);
        m.roughness = 0.5;
      }
      const inDesk = /desk|keyboard|mouse|monitor|pad|room/i.test(pathOf(o));
      o.castShadow = name !== 'wall' && name !== 'floor';
      o.receiveShadow = inDesk;
      if (name === 'fan_blade') m.transparent = false;
    }
  });

  // лопасти на оборотах становятся полупрозрачными, поверх — диск-размытие
  const cv = document.createElement('canvas');
  cv.width = cv.height = 256;
  const cg = cv.getContext('2d');
  cg.fillStyle = '#000'; cg.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 180; i++) {
    const a0 = (i / 180) * Math.PI * 2, v = 120 + Math.random() * 135 | 0;
    cg.fillStyle = 'rgb(' + v + ',' + v + ',' + v + ')';
    cg.beginPath(); cg.moveTo(128, 128); cg.arc(128, 128, 128, a0, a0 + Math.PI * 2 / 180 + 0.01); cg.fill();
  }
  const blurTex = new THREE.CanvasTexture(cv);
  S.discMat = new THREE.MeshStandardMaterial({ color: 0x0b0b0d, roughness: 0.35, transparent: true, opacity: 0, alphaMap: blurTex, side: THREE.DoubleSide, depthWrite: false });
  for (const r of S.rotors) {
    r.node.traverse((c) => { if (c.isMesh && c.material.name === 'fan_blade') r.blades.push(c); });
    for (const b of r.blades) {
      if (!S.bladeMat) { S.bladeMat = b.material.clone(); S.bladeMat.transparent = true; }
      b.material = S.bladeMat;
    }
    const disc = new THREE.Mesh(new THREE.RingGeometry(r.gpu ? 0.0142 : 0.0212, r.gpu ? 0.0422 : 0.055, 72, 1), S.discMat);
    disc.rotation.x = -Math.PI / 2;
    disc.position.y = 0.0008;
    disc.renderOrder = 2;
    r.node.add(disc);
  }

  // --- свет
  const add = (light, on, delay, tag) => { scene.add(light); S.lights.push({ light, on, delay, tag }); light.intensity = 0; return light; };
  const pl = (pos, color, on, dist, delay, tag) => { const l = new THREE.PointLight(color, 0, dist, 2.0); l.position.copy(pos); if (color === ACCENT) S.accent.lights.push(l); return add(l, on, delay, tag); };
  // внутри корпуса
  pl(B(-115, -41, 440), ACCENT, 0.16, 0.9, 0.5);
  pl(B(5, -41, 440), ACCENT, 0.16, 0.9, 0.7);
  pl(B(125, -41, 440), ACCENT, 0.16, 0.9, 0.9);
  pl(B(-190, -30, 380), ACCENT, 0.1, 0.7, 1.0);
  pl(B(-120, -60, 265), WHITE, 0.05, 0.6, 1.4);
  pl(B(193, -70, 300), ACCENT, 0.22, 0.8, 1.1);
  // лента за столом: заливает стену
  {
    const l = new THREE.RectAreaLight(ACCENT, 0, 1.5, 0.05);
    l.position.copy(B(-386, -620, -40));
    l.lookAt(B(-1400, -620, 600));
    add(l, 14, 2.4, 'wall');
    S.accent.lights.push(l);
  }
  // световая планка над монитором: тёплый свет на стол, с тенью (тень считается один раз)
  {
    const bar = new THREE.SpotLight(WARM, 0, 2.2, 1.0, 0.9, 2.0);
    const p = new THREE.Vector3();
    (S.nodes.a_bar || root).getWorldPosition(p);
    bar.position.copy(p);
    bar.target.position.copy(B(170, -620, 0));
    bar.castShadow = true;
    bar.shadow.mapSize.set(1024, 1024);
    bar.shadow.camera.near = 0.05;
    bar.shadow.camera.far = 2.2;
    bar.shadow.bias = -0.0006;
    bar.shadow.normalBias = 0.002;
    scene.add(bar.target);
    add(bar, 2.8, 3.0, 'bar');
  }
  // пузырьки в резервуаре
  {
    const n = 34;
    const geo = new THREE.SphereGeometry(1, 8, 6);
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color().setRGB(1.0, 0.62, 0.45), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
    const im = new THREE.InstancedMesh(geo, mat, n);
    im.frustumCulled = false;
    im.renderOrder = 5;
    scene.add(im);
    S.noAO.push(im);
    S.bubbles = { im, mat, list: Array.from({ length: n }, () => ({ a: Math.random() * 6.28, r: Math.random() * 0.02, y: Math.random(), v: 0.05 + Math.random() * 0.09, s: 0.0007 + Math.random() * 0.0013, ph: Math.random() * 6 })) };
  }
  // монитор светит на стол и клавиатуру
  const ml = new THREE.RectAreaLight(0x9fb4e8, 0, 0.597, 0.336);
  ml.position.copy(B(-180, -620, 309));
  ml.lookAt(B(800, -620, 250));
  add(ml, 4.0, 3.4, 'monitor');
  S.monitorLight = ml;
  // слабый «лунный» свет из окна, чтобы выключенная сцена не была чёрной
  const moon = new THREE.DirectionalLight(0x8aa4d8, 1.1);
  moon.position.copy(B(1600, -900, 1700));
  moon.target.position.copy(B(0, -200, 200));
  scene.add(moon, moon.target);
  const fill = new THREE.HemisphereLight(0x2a3040, 0x0a0806, 0.7);
  scene.add(fill);
}

const M4 = new THREE.Matrix4();
function pathOf(o) { let s = ''; for (let p = o; p; p = p.parent) s += '/' + p.name; return s; }

// ---------- кадр

function update(S, dt, t) {
  S.time = t;
  const since = S.onSince == null ? -1 : t - S.onSince;
  const on = since >= 0;
  const power = on ? S.power : 0;
  // светодиоды: волна включения + лёгкое дыхание
  for (const L of S.leds) {
    const a = on ? smooth(L.delay, L.delay + 0.9, since) : 0;
    const flick = on && since < L.delay + 0.5 ? 0.6 + 0.4 * Math.sin(since * 60 + L.delay * 40) : 1;
    L.m.emissiveIntensity = L.k * a * flick * power;
  }
  for (const L of S.lights) {
    const a = on ? smooth(L.delay, L.delay + 1.4, since) : 0;
    L.light.intensity = L.on * a * power;
  }
  if (S.powerLed) {
    const v = THREE.MathUtils.lerp(0.35 + 0.3 * Math.sin(t * 1.6), 2.2, power);
    for (const m of S.powerLed) m.emissiveIntensity = Math.max(0.05, v);
  }
  if (S.coolant) {
    S.coolant.userData.u.uTime.value = t;
    S.coolant.userData.u.uGlow.value = 0.06 + 1.5 * smooth(0.8, 3.2, since) * power;
  }
  // вентиляторы: раскрутка
  const spin = smooth(0.2, 3.6, since) * power;
  S.spin = spin;
  if (S.bladeMat) { S.bladeMat.opacity = 1 - 0.68 * spin; S.discMat.opacity = 0.6 * spin; }
  for (const r of S.rotors) {
    const speed = (r.gpu ? 22.0 : 27.0) * spin;
    r.angle += speed * dt;
    r.node.rotation.y = r.angle;
  }
  if (S.bubbles) {
    const { im, mat, list } = S.bubbles;
    mat.opacity = 0.55 * smooth(1.5, 4, since) * power;
    if (power > 0) {
      for (let i = 0; i < list.length; i++) {
        const b = list[i];
        b.y += b.v * dt * 0.6 * power;
        if (b.y > 1) { b.y = 0; b.a = Math.random() * 6.28; b.r = Math.random() * 0.021; }
        const wob = 0.0012 * Math.sin(t * 3 + b.ph);
        M4.makeScale(b.s, b.s, b.s);
        // ось резервуара: (193, −20) мм; жидкость от 191 до 368 мм по высоте
        M4.setPosition(0.193 + Math.cos(b.a) * b.r + wob, 0.191 + b.y * 0.176, 0.02 + Math.sin(b.a) * b.r);
        im.setMatrixAt(i, M4);
      }
      im.instanceMatrix.needsUpdate = true;
    }
  }
  S.scene.environmentIntensity = 0.75 + 0.15 * smooth(0.5, 3, since) * power;
}

// ---------- текстуры, которые строятся на лету

// карта нормалей оплётки: две диагональные пряди, идущие поочерёдно сверху и снизу
function braidTexture() {
  const N = 64, P = 16, h = new Float32Array(N * N), data = new Uint8Array(N * N * 4);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const a = ((x + y) / P) % 1, b = (((x - y) / P) % 1 + 1) % 1;
    const sa = Math.sin(Math.PI * a), sb = Math.sin(Math.PI * b);
    const over = (Math.floor((x + y) / P) + Math.floor((x - y + N * 4) / P)) % 2;
    h[y * N + x] = over ? Math.max(sa, 0.55 * sb) : Math.max(sb, 0.55 * sa);
  }
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const dx = h[y * N + (x + 1) % N] - h[y * N + (x + N - 1) % N];
    const dy = h[((y + 1) % N) * N + x] - h[((y + N - 1) % N) * N + x];
    const nx = -dx * 2.2, ny = -dy * 2.2, l = Math.hypot(nx, ny, 1), i = (y * N + x) * 4;
    data[i] = (nx / l * 0.5 + 0.5) * 255; data[i + 1] = (ny / l * 0.5 + 0.5) * 255; data[i + 2] = (1 / l * 0.5 + 0.5) * 255; data[i + 3] = 255;
  }
  const t = new THREE.DataTexture(data, N, N);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(3, 1);
  t.generateMipmaps = true;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.magFilter = THREE.LinearFilter;
  t.anisotropy = 4;
  t.needsUpdate = true;
  return t;
}

// рисунок дорожек на текстолите: пучки параллельных проводников с изломами под 45° и переходные отверстия
function pcbTexture(renderer) {
  const N = 2048, c = document.createElement('canvas');
  c.width = c.height = N;
  const g = c.getContext('2d');
  g.fillStyle = '#0b0e0d'; g.fillRect(0, 0, N, N);
  let seed = 5;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  g.lineCap = 'round'; g.lineJoin = 'round';
  for (let k = 0; k < 150; k++) {
    const n = 2 + Math.floor(rnd() * 9), gap = 5 + rnd() * 3;
    let x = rnd() * N, y = rnd() * N;
    const dir = Math.floor(rnd() * 4);
    const steps = [];
    let d = dir;
    for (let i = 0; i < 3 + Math.floor(rnd() * 4); i++) { steps.push([d, 60 + rnd() * 320]); d = (d + (rnd() < 0.5 ? 1 : 7)) % 8; }
    g.strokeStyle = rnd() < 0.5 ? '#161c1a' : '#131817';
    g.lineWidth = 2.2;
    for (let j = 0; j < n; j++) {
      let px = x, py = y;
      g.beginPath();
      // смещение дорожки поперёк первого направления
      const a0 = steps[0][0] * Math.PI / 4;
      px += -Math.sin(a0) * j * gap; py += Math.cos(a0) * j * gap;
      g.moveTo(px, py);
      for (const [dd, len] of steps) { const a = dd * Math.PI / 4; px += Math.cos(a) * len; py += Math.sin(a) * len; g.lineTo(px, py); }
      g.stroke();
      g.fillStyle = '#252c2a'; g.beginPath(); g.arc(px, py, 4.2, 0, 7); g.fill();
      g.fillStyle = '#060807'; g.beginPath(); g.arc(px, py, 1.7, 0, 7); g.fill();
    }
  }
  for (let i = 0; i < 900; i++) {
    const x = rnd() * N, y = rnd() * N;
    g.fillStyle = '#222927'; g.beginPath(); g.arc(x, y, 3.4, 0, 7); g.fill();
    g.fillStyle = '#060807'; g.beginPath(); g.arc(x, y, 1.4, 0, 7); g.fill();
  }
  g.fillStyle = '#0b0e0d'; g.fillRect(0, 0, 6, 6);     // для деталей без развёртки — ровный цвет
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.flipY = false;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  return t;
}
