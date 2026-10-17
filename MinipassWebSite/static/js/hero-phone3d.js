/* 3D phone for the landing hero (three.js, real geometry, real lighting).
   Pixel 9 proportions in millimetres. The hero timeline drives window.MPH_P3
   (ry, rx, dist, streak) and calls window.phone3d.render() on every update. */
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/RoundedBoxGeometry.js';

const canvas = document.getElementById('mphPhone3d');
if (canvas) init(canvas);

function init(canvas) {
  const BODY = { w: 72, h: 152.8, d: 8.5, r: 10.2 };
  const GLASS = { w: 70.8, h: 151.6, r: 9.6 };
  const SCREEN = { w: 66.8, h: 147.4, r: 7.8 };
  const HOLE = { y: 3.9, r: 1.55 };
  const FOV = 22;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;

  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const camera = new THREE.PerspectiveCamera(FOV, 1, 1, 3000);

  function roundedShape(w, h, r) {
    const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
    s.moveTo(x + r, y);
    s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
    s.lineTo(x + w, y + h - r); s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    s.lineTo(x + r, y + h); s.quadraticCurveTo(x, y + h, x, y + h - r);
    s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
    return s;
  }
  function planarUV(geo, w, h) {
    const p = geo.attributes.position, uv = [];
    for (let i = 0; i < p.count; i++) uv.push(p.getX(i) / w + .5, p.getY(i) / h + .5);
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    return geo;
  }

  const phone = new THREE.Group();
  scene.add(phone);

  /* satin aluminium frame */
  const bevel = 1.3;
  const bodyGeo = new THREE.ExtrudeGeometry(roundedShape(BODY.w - 2 * bevel, BODY.h - 2 * bevel, BODY.r - bevel), {
    depth: BODY.d - 2 * bevel, bevelEnabled: true, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 8, curveSegments: 40 });
  bodyGeo.translate(0, 0, -(BODY.d - 2 * bevel) / 2);
  const metal = new THREE.MeshPhysicalMaterial({ color: 0x9a9da5, metalness: 1, roughness: .2, clearcoat: .6, clearcoatRoughness: .12, envMapIntensity: 1.4 });
  phone.add(new THREE.Mesh(bodyGeo, metal));
  const FRONT = BODY.d / 2;

  /* power and volume buttons on the right edge */
  const btnMat = new THREE.MeshPhysicalMaterial({ color: 0x9a9da5, metalness: 1, roughness: .22, envMapIntensity: 1.4 });
  const power = new THREE.Mesh(new RoundedBoxGeometry(1.6, 11, 3.2, 3, .7), btnMat);
  power.position.set(BODY.w / 2 + .2, 30, 0); phone.add(power);
  const volume = new THREE.Mesh(new RoundedBoxGeometry(1.6, 21, 3.2, 3, .7), btnMat);
  volume.position.set(BODY.w / 2 + .2, 6, 0); phone.add(volume);

  /* black front glass */
  const glass = new THREE.Mesh(new THREE.ShapeGeometry(roundedShape(GLASS.w, GLASS.h, GLASS.r), 40),
    new THREE.MeshPhysicalMaterial({ color: 0x050506, roughness: .05, metalness: 0, clearcoat: 1, clearcoatRoughness: .03 }));
  glass.position.z = FRONT + .02; phone.add(glass);

  /* the screen: the real Minipass mobile app, drawn into a canvas so the Revenue number can be repainted live.
     Revenue value measured in the app (412 px wide layout, 1080 px texture, 126 px status bar on top):
     centred at x 164.03, Inter 700 24px, white card behind it. */
  const SX = 1080 / 412, BAR = 126;
  const REV = { cx: 164.03 * SX, base: BAR + 233.8 * SX, size: 24 * SX,
                patch: [280, 672, 300, 88] };            /* x, y, w, h in texture px: covers the captured number */
  const scr = document.createElement('canvas'); scr.width = 1080; scr.height = 2384;
  const sctx = scr.getContext('2d');
  const base = new Image();
  let revText = window.MPH_REV_TEXT || '$32,405';
  const tex = new THREE.CanvasTexture(scr);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
  function paintRevenue() {
    const [x, y, w, h] = REV.patch;
    sctx.fillStyle = '#ffffff'; sctx.fillRect(x, y, w, h);  /* clear the captured number (white card) */
    sctx.fillStyle = 'oklch(0.145 0 0)';
    sctx.font = `700 ${REV.size}px 'MPH Inter', Inter, sans-serif`;
    sctx.fontVariant = 'normal';
    sctx.textAlign = 'center'; sctx.textBaseline = 'alphabetic';
    sctx.fillText(revText, REV.cx, REV.base);
    tex.needsUpdate = true;
  }
  Promise.all([
    new Promise((ok) => { base.onload = ok; base.src = canvas.dataset.screen; }),
    document.fonts ? document.fonts.load(`700 ${REV.size}px 'MPH Inter'`).catch(() => {}) : Promise.resolve()
  ]).then(() => { sctx.drawImage(base, 0, 0); paintRevenue(); ready = true; render(); });
  const screen = new THREE.Mesh(planarUV(new THREE.ShapeGeometry(roundedShape(SCREEN.w, SCREEN.h, SCREEN.r), 40), SCREEN.w, SCREEN.h),
    new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
  screen.position.z = FRONT + .05; phone.add(screen);

  /* punch-hole camera, inside the status bar */
  const holeY = SCREEN.h / 2 - HOLE.y;
  const ring = new THREE.Mesh(new THREE.CircleGeometry(HOLE.r + .35, 48), new THREE.MeshBasicMaterial({ color: 0x1a1a1c }));
  ring.position.set(0, holeY, FRONT + .07); phone.add(ring);
  const hole = new THREE.Mesh(new THREE.CircleGeometry(HOLE.r, 48), new THREE.MeshPhysicalMaterial({ color: 0x030304, roughness: .1, clearcoat: 1 }));
  hole.position.set(0, holeY, FRONT + .08); phone.add(hole);

  /* light streak on the glass; the timeline slides it across */
  const sc = document.createElement('canvas'); sc.width = 512; sc.height = 1024;
  {
    const g = sc.getContext('2d'), grad = g.createLinearGradient(0, 0, 512, 1024);
    grad.addColorStop(0, 'rgba(255,255,255,0)');
    grad.addColorStop(.40, 'rgba(255,255,255,0)');
    grad.addColorStop(.46, 'rgba(255,255,255,.08)');
    grad.addColorStop(.52, 'rgba(255,255,255,.15)');
    grad.addColorStop(.62, 'rgba(255,255,255,.03)');
    grad.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = grad; g.fillRect(0, 0, 512, 1024);
  }
  const streakTex = new THREE.CanvasTexture(sc);
  const streak = new THREE.Mesh(planarUV(new THREE.ShapeGeometry(roundedShape(GLASS.w, GLASS.h, GLASS.r), 40), GLASS.w, GLASS.h),
    new THREE.MeshBasicMaterial({ map: streakTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
  streak.position.z = FRONT + .12; phone.add(streak);

  const key = new THREE.DirectionalLight(0xffffff, 1.4); key.position.set(-120, 160, 220); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffffff, 2.2); rim.position.set(260, 60, -60); scene.add(rim);

  let ready = false;
  const state = window.MPH_P3 || { ry: -.22, rx: .04, dist: 441.4, streak: 0 };

  function size() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    const shown = canvas.getBoundingClientRect().width || w;            /* the stage is scaled with CSS */
    renderer.setPixelRatio(Math.min((window.devicePixelRatio || 1) * (shown / w), 3));
    renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  function render() {
    const s = window.MPH_P3 || state;
    phone.rotation.set(s.rx, s.ry, 0);
    streakTex.offset.set(s.streak, s.streak * 2);
    camera.position.set(0, 0, s.dist); camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  }
  size(); render();
  window.addEventListener('resize', () => { size(); render(); });
  function setRevenue(txt) {
    if (txt === revText) return;
    revText = txt;
    if (ready) { paintRevenue(); render(); }
  }
  window.phone3d = { render, resize: () => { size(); render(); }, isReady: () => ready, setRevenue,
                     _rev: REV, _paint: () => { paintRevenue(); render(); } };   /* _rev/_paint: calibration only */
}
