/**
 * Apex Ledger — nebula gate morphs into an apex-predator spine after breach.
 */
(function () {
  const canvas = document.getElementById("cosmos-canvas");
  if (!canvas || typeof THREE === "undefined") return;

  const wrap = document.getElementById("cosmos-wrap") || canvas.parentElement;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x060a12, 0.028);

  const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 140);
  camera.position.set(0, 0, 20);

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x060a12, 1);

  function gauss() {
    return (Math.random() + Math.random() + Math.random()) / 3 - 0.5;
  }

  function ease(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  const spinePalette = [
    new THREE.Color("#7dd3fc"),
    new THREE.Color("#5eead4"),
    new THREE.Color("#93c5fd"),
    new THREE.Color("#bae6fd"),
  ];
  const cloudPalette = [
    new THREE.Color("#67e8f9"),
    new THREE.Color("#818cf8"),
    new THREE.Color("#a5b4fc"),
  ];

  function buildSpineTargets(count) {
    const targets = [];
    const spineX = -11;
    const verts = Math.max(40, Math.floor(count * 0.32));
    const ribs = Math.max(60, Math.floor(count * 0.48));
    const apexN = count - verts - ribs;

    for (let i = 0; i < verts; i++) {
      const t = i / Math.max(verts - 1, 1);
      const y = (t - 0.46) * 42;
      const curve = Math.sin(t * Math.PI * 3.2) * 1.1;
      targets.push({ x: spineX + curve, y, z: 4 + Math.cos(t * Math.PI * 2.5) * 1.4 });
    }

    for (let i = 0; i < ribs; i++) {
      const vi = Math.floor((i / ribs) * (verts - 1));
      const base = targets[vi];
      const side = i % 2 === 0 ? 1 : -1;
      const reach = 1.8 + (i % 5) * 0.55;
      targets.push({
        x: base.x + side * reach,
        y: base.y + gauss() * 0.6,
        z: base.z + gauss() * 1.2,
      });
    }

    const apexY = targets[verts - 1].y + 1.5;
    for (let i = 0; i < apexN; i++) {
      const a = (i / Math.max(apexN - 1, 1)) * Math.PI - Math.PI / 2;
      const r = 1.2 + (i % 7) * 0.35;
      targets.push({
        x: spineX + Math.cos(a) * r * 0.55,
        y: apexY + Math.sin(a) * r + 1.8,
        z: 5.5 + (i % 3) * 0.4,
      });
    }

    while (targets.length < count) {
      const t = targets.length % verts;
      targets.push({ ...targets[t], z: targets[t].z + gauss() * 0.5 });
    }
    return targets.slice(0, count);
  }

  function makeMorphCloud(count) {
    const start = new Float32Array(count * 3);
    const spine = buildSpineTargets(count);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      start[i * 3] = gauss() * 22;
      start[i * 3 + 1] = gauss() * 16;
      start[i * 3 + 2] = gauss() * 14 + 6;
      const c = cloudPalette[Math.floor(Math.random() * cloudPalette.length)];
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(start.slice(), 3));
    geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geo.userData.start = start.slice();
    geo.userData.spine = spine;
    return geo;
  }

  const starCount = reduced ? 500 : 1200;
  const starStart = new Float32Array(starCount * 3);
  const starColors = new Float32Array(starCount * 3);
  for (let i = 0; i < starCount; i++) {
    starStart[i * 3] = (Math.random() - 0.5) * 100;
    starStart[i * 3 + 1] = (Math.random() - 0.5) * 60;
    starStart[i * 3 + 2] = (Math.random() - 0.5) * 80 - 10;
    const g = 0.55 + Math.random() * 0.35;
    starColors[i * 3] = g;
    starColors[i * 3 + 1] = g + 0.08;
    starColors[i * 3 + 2] = g + 0.15;
  }
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute("position", new THREE.BufferAttribute(starStart, 3));
  starGeo.setAttribute("color", new THREE.BufferAttribute(starColors, 3));
  const starMat = new THREE.PointsMaterial({
    size: reduced ? 0.1 : 0.16,
    vertexColors: true,
    transparent: true,
    opacity: 0.55,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const stars = new THREE.Points(starGeo, starMat);
  scene.add(stars);

  const morphCount = reduced ? 700 : 2000;
  const morphGeo = makeMorphCloud(morphCount);
  const morphMat = new THREE.PointsMaterial({
    size: reduced ? 0.45 : 0.85,
    vertexColors: true,
    transparent: true,
    opacity: 0.92,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  });
  const morphCloud = new THREE.Points(morphGeo, morphMat);
  scene.add(morphCloud);

  const spineLineMat = new THREE.LineBasicMaterial({
    color: 0x5eead4,
    transparent: true,
    opacity: 0,
  });
  const spineLineGeo = new THREE.BufferGeometry();
  const spineLine = new THREE.Line(spineLineGeo, spineLineMat);
  scene.add(spineLine);

  let gateOpen = 0;
  let gateTarget = 0;
  let mouseX = 0;
  let mouseY = 0;

  window.addEventListener("pointermove", (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
  });

  function resize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }
  window.addEventListener("resize", resize);

  function breachGate() {
    gateTarget = 1;
    document.body.classList.remove("gate-locked");
    document.body.classList.add("gate-open");
    wrap?.classList.add("breached");
    document.getElementById("cosmos-gate")?.classList.add("breached");
  }

  window.ApexCosmos = { breachGate, isOpen: () => gateOpen > 0.92 };
  document.getElementById("gate-breach")?.addEventListener("click", breachGate);

  function updateMorph() {
    const morph = ease(gateOpen);
    const cloudMorph = 1 - morph;
    const pos = morphGeo.getAttribute("position");
    const col = morphGeo.getAttribute("color");
    const start = morphGeo.userData.start;
    const spine = morphGeo.userData.spine;
    const linePts = [];

    for (let i = 0; i < morphCount; i++) {
      const sx = start[i * 3];
      const sy = start[i * 3 + 1];
      const sz = start[i * 3 + 2];
      const tx = spine[i].x;
      const ty = spine[i].y;
      const tz = spine[i].z;

      const spread = 1 + cloudMorph * 2.2;
      const cx = sx * spread;
      const cy = sy * spread;
      const cz = sz * spread + cloudMorph * 4;

      pos.array[i * 3] = cx * cloudMorph + tx * morph;
      pos.array[i * 3 + 1] = cy * cloudMorph + ty * morph;
      pos.array[i * 3 + 2] = cz * cloudMorph + tz * morph;

      const cp = cloudPalette[i % cloudPalette.length];
      const sp = spinePalette[i % spinePalette.length];
      col.array[i * 3] = cp.r * cloudMorph + sp.r * morph;
      col.array[i * 3 + 1] = cp.g * cloudMorph + sp.g * morph;
      col.array[i * 3 + 2] = cp.b * cloudMorph + sp.b * morph;

      if (i < spine.length * 0.32 && morph > 0.5) {
        linePts.push(tx, ty, tz);
      }
    }
    pos.needsUpdate = true;
    col.needsUpdate = true;

    morphMat.opacity = 0.95 * (0.35 + cloudMorph * 0.65 + morph * 0.45);
    morphMat.size = (reduced ? 0.45 : 0.85) * (0.7 + morph * 0.55);

    if (linePts.length > 6) {
      spineLineGeo.setAttribute("position", new THREE.Float32BufferAttribute(linePts, 3));
      spineLineMat.opacity = morph * 0.35;
    } else {
      spineLineMat.opacity = 0;
    }
  }

  let t = 0;
  function animate() {
    requestAnimationFrame(animate);
    t += reduced ? 0.002 : 0.006;
    gateOpen += (gateTarget - gateOpen) * 0.04;
    updateMorph();

    const morph = ease(gateOpen);
    morphCloud.rotation.y = t * 0.08 * (1 - morph * 0.85);
    morphCloud.rotation.z = Math.sin(t * 0.35) * 0.04 * (1 - morph);
    stars.rotation.y = t * 0.04;

    camera.position.z = 20 - morph * 5;
    const targetX = -3.5 * morph + mouseX * (2.2 - morph);
    const targetY = -mouseY * (2 - morph);
    camera.position.x += (targetX - camera.position.x) * 0.03;
    camera.position.y += (targetY - camera.position.y) * 0.03;
    camera.lookAt(-4 * morph, morph * 2, 0);

    starMat.opacity = 0.4 + morph * 0.25;
    renderer.render(scene, camera);
  }
  animate();

  document.querySelectorAll(".holo-panel, .holo-tile, .appbar").forEach((el) => {
    el.addEventListener("mousemove", (e) => {
      if (!document.body.classList.contains("gate-open")) return;
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      el.style.setProperty("--tilt-x", `${-y * 3}deg`);
      el.style.setProperty("--tilt-y", `${x * 3}deg`);
    });
    el.addEventListener("mouseleave", () => {
      el.style.setProperty("--tilt-x", "0deg");
      el.style.setProperty("--tilt-y", "0deg");
    });
  });
})();
