/**
 * Apex Ledger — particle field morphs into an anatomical human spine (side view).
 */
(function () {
  const canvas = document.getElementById("cosmos-canvas");
  if (!canvas || typeof THREE === "undefined") return;

  const wrap = document.getElementById("cosmos-wrap") || canvas.parentElement;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x050810, 0.024);

  const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 150);
  camera.position.set(0, 0, 22);

  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x050810, 1);

  function gauss() {
    return (Math.random() + Math.random() + Math.random()) / 3 - 0.5;
  }

  function ease(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  /** Lumbar lordosis → thoracic kyphosis → cervical lordosis (side view). */
  function spinalOffset(t) {
    if (t < 0.33) {
      const u = t / 0.33;
      return -Math.sin(u * Math.PI) * 2.6;
    }
    if (t < 0.68) {
      const u = (t - 0.33) / 0.35;
      return Math.sin(u * Math.PI) * 2.15;
    }
    const u = (t - 0.68) / 0.32;
    return -Math.sin(u * Math.PI) * 1.75;
  }

  const bonePalette = [
    new THREE.Color("#e2e8f0"),
    new THREE.Color("#cbd5e1"),
    new THREE.Color("#7dd3fc"),
    new THREE.Color("#5eead4"),
    new THREE.Color("#bae6fd"),
  ];
  const glowPalette = [
    new THREE.Color("#22d3ee"),
    new THREE.Color("#67e8f9"),
    new THREE.Color("#a5f3fc"),
  ];
  const cloudPalette = [
    new THREE.Color("#6366f1"),
    new THREE.Color("#818cf8"),
    new THREE.Color("#22d3ee"),
  ];

  function buildHumanSpine(count) {
    const targets = [];
    const vertebraPath = [];
    const spineX = -10.5;
    const segments = 32;

    for (let s = 0; s <= segments; s++) {
      const t = s / segments;
      const y = (t - 0.5) * 40;
      vertebraPath.push({ x: spineX + spinalOffset(t), y, z: 3.6 });
    }

    const vertN = Math.floor(count * 0.26);
    const discN = Math.floor(count * 0.08);
    const ribN = Math.floor(count * 0.38);
    const pelvisN = Math.floor(count * 0.1);
    const skullN = count - vertN - discN - ribN - pelvisN;

    for (let i = 0; i < vertN; i++) {
      const seg = i % segments;
      const t = seg / segments;
      const y = (t - 0.5) * 40;
      const cx = spineX + spinalOffset(t);
      const ring = (i % 9) / 9;
      const r = 0.28 + (i % 3) * 0.06;
      targets.push({
        x: cx + Math.cos(ring * Math.PI * 2) * r,
        y: y + Math.sin(ring * Math.PI * 2) * 0.15,
        z: 3.2 + Math.sin(ring * Math.PI * 2) * 0.5,
        kind: "vert",
      });
    }

    for (let i = 0; i < discN; i++) {
      const t = ((i + 0.5) / discN) * 0.92 + 0.04;
      const y = (t - 0.5) * 40;
      targets.push({
        x: spineX + spinalOffset(t) + gauss() * 0.2,
        y: y + gauss() * 0.15,
        z: 3.45 + gauss() * 0.25,
        kind: "disc",
      });
    }

    const ribsPerSide = Math.max(5, Math.floor(ribN / 24));
    for (let r = 0; r < 12; r++) {
      const t = 0.36 + (r / 11) * 0.3;
      const y = (t - 0.5) * 40;
      const cx = spineX + spinalOffset(t);
      const len = 2.6 + (r % 4) * 0.45;
      for (const side of [-1, 1]) {
        for (let p = 0; p < ribsPerSide; p++) {
          const u = p / ribsPerSide;
          const arch = Math.sin(u * Math.PI * 0.85);
          targets.push({
            x: cx + side * (0.3 + u * len),
            y: y - u * u * 1.5 + arch * 0.55,
            z: 2.6 + arch * 1.8 + (side * 0.15),
            kind: "rib",
          });
        }
      }
    }

    for (let i = 0; i < pelvisN; i++) {
      const u = i / Math.max(pelvisN - 1, 1);
      const y = -20.5 - u * 3.2;
      const spread = (u - 0.5) * 3.2;
      targets.push({
        x: spineX + spinalOffset(0.02) + spread,
        y,
        z: 3.1 + u * 0.5,
        kind: "pelvis",
      });
    }

    const headY = vertebraPath[vertebraPath.length - 1].y + 2.4;
    const headX = spineX + spinalOffset(1);
    for (let i = 0; i < skullN; i++) {
      const a = (i / skullN) * Math.PI * 2;
      const rx = 1.5 + (i % 4) * 0.12;
      const ry = 2.1 + (i % 5) * 0.1;
      targets.push({
        x: headX + Math.cos(a) * rx * (a > Math.PI ? 0.85 : 1),
        y: headY + Math.sin(a) * ry,
        z: 3.9 + Math.sin(a * 2) * 0.65,
        kind: "skull",
      });
    }

    while (targets.length < count) {
      const v = targets.length % Math.max(vertN, 1);
      targets.push({ ...targets[v] });
    }

    return { targets: targets.slice(0, count), vertebraPath };
  }

  function makeMorphCloud(count) {
    const start = new Float32Array(count * 3);
    const { targets, vertebraPath } = buildHumanSpine(count);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      start[i * 3] = gauss() * 24;
      start[i * 3 + 1] = gauss() * 18;
      start[i * 3 + 2] = gauss() * 16 + 8;
      const c = cloudPalette[Math.floor(Math.random() * cloudPalette.length)];
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(start.slice(), 3));
    geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geo.userData.start = start.slice();
    geo.userData.spine = targets;
    geo.userData.vertebraPath = vertebraPath;
    return geo;
  }

  const starCount = reduced ? 600 : 1400;
  const starStart = new Float32Array(starCount * 3);
  const starColors = new Float32Array(starCount * 3);
  for (let i = 0; i < starCount; i++) {
    starStart[i * 3] = (Math.random() - 0.5) * 110;
    starStart[i * 3 + 1] = (Math.random() - 0.5) * 65;
    starStart[i * 3 + 2] = (Math.random() - 0.5) * 85 - 12;
    const g = 0.5 + Math.random() * 0.4;
    starColors[i * 3] = g;
    starColors[i * 3 + 1] = g + 0.06;
    starColors[i * 3 + 2] = g + 0.12;
  }
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute("position", new THREE.BufferAttribute(starStart, 3));
  starGeo.setAttribute("color", new THREE.BufferAttribute(starColors, 3));
  const starMat = new THREE.PointsMaterial({
    size: reduced ? 0.08 : 0.14,
    vertexColors: true,
    transparent: true,
    opacity: 0.5,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  scene.add(new THREE.Points(starGeo, starMat));

  const morphCount = reduced ? 900 : 2400;
  const morphGeo = makeMorphCloud(morphCount);
  const morphMat = new THREE.PointsMaterial({
    size: reduced ? 0.38 : 0.68,
    vertexColors: true,
    transparent: true,
    opacity: 0.94,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
  });
  const morphCloud = new THREE.Points(morphGeo, morphMat);
  scene.add(morphCloud);

  const spineLineMat = new THREE.LineBasicMaterial({ color: 0x94a3b8, transparent: true, opacity: 0 });
  const spineLineGeo = new THREE.BufferGeometry();
  const spineLine = new THREE.Line(spineLineGeo, spineLineMat);
  scene.add(spineLine);

  const canalMat = new THREE.LineBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0 });
  const canalGeo = new THREE.BufferGeometry();
  const canalLine = new THREE.Line(canalGeo, canalMat);
  scene.add(canalLine);

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
    const breath = gateOpen > 0.9 ? Math.sin(Date.now() * 0.0012) * 0.04 : 0;
    const pos = morphGeo.getAttribute("position");
    const col = morphGeo.getAttribute("color");
    const start = morphGeo.userData.start;
    const spine = morphGeo.userData.spine;
    const path = morphGeo.userData.vertebraPath;

    for (let i = 0; i < morphCount; i++) {
      const sx = start[i * 3];
      const sy = start[i * 3 + 1];
      const sz = start[i * 3 + 2];
      const pt = spine[i];
      const tx = pt.x;
      const ty = pt.y * (1 + breath);
      const tz = pt.z;

      const spread = 1 + cloudMorph * 2.4;
      pos.array[i * 3] = sx * spread * cloudMorph + tx * morph;
      pos.array[i * 3 + 1] = sy * spread * cloudMorph + ty * morph;
      pos.array[i * 3 + 2] = (sz * spread + cloudMorph * 5) * cloudMorph + tz * morph;

      const cp = cloudPalette[i % cloudPalette.length];
      const bp = pt.kind === "disc" ? glowPalette[i % glowPalette.length] : bonePalette[i % bonePalette.length];
      col.array[i * 3] = cp.r * cloudMorph + bp.r * morph;
      col.array[i * 3 + 1] = cp.g * cloudMorph + bp.g * morph;
      col.array[i * 3 + 2] = cp.b * cloudMorph + bp.b * morph;
    }
    pos.needsUpdate = true;
    col.needsUpdate = true;

    morphMat.opacity = 0.96 * (0.3 + cloudMorph * 0.7 + morph * 0.55);
    morphMat.size = (reduced ? 0.38 : 0.68) * (0.7 + morph * 0.5);

    if (morph > 0.4 && path?.length) {
      const linePts = [];
      const canalPts = [];
      path.forEach((p) => {
        linePts.push(p.x, p.y * (1 + breath), p.z);
        canalPts.push(p.x + 0.35, p.y * (1 + breath), p.z + 0.15);
      });
      spineLineGeo.setAttribute("position", new THREE.Float32BufferAttribute(linePts, 3));
      canalGeo.setAttribute("position", new THREE.Float32BufferAttribute(canalPts, 3));
      spineLineMat.opacity = morph * 0.45;
      canalMat.opacity = morph * 0.22;
    } else {
      spineLineMat.opacity = 0;
      canalMat.opacity = 0;
    }
  }

  let t = 0;
  function animate() {
    requestAnimationFrame(animate);
    t += reduced ? 0.002 : 0.005;
    gateOpen += (gateTarget - gateOpen) * 0.038;
    updateMorph();

    const morph = ease(gateOpen);
    morphCloud.rotation.y = t * 0.06 * (1 - morph * 0.9);
    morphCloud.rotation.z = Math.sin(t * 0.28) * 0.03 * (1 - morph);

    camera.position.z = 22 - morph * 6;
    const targetX = -4 * morph + mouseX * (2.4 - morph);
    const targetY = -mouseY * (2.2 - morph);
    camera.position.x += (targetX - camera.position.x) * 0.032;
    camera.position.y += (targetY - camera.position.y) * 0.032;
    camera.lookAt(-4.5 * morph, morph * 1.5, 0);

    renderer.render(scene, camera);
  }
  animate();

  document.querySelectorAll(".holo-panel, .holo-tile, .appbar, .bluf-banner").forEach((el) => {
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
