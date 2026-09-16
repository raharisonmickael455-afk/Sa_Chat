(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const coarsePointer = window.matchMedia("(pointer: coarse)");
  const touchDevice = coarsePointer.matches;
  const mobileBudget = touchDevice || (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 4);
  const maxParticles = mobileBudget ? 24 : 72;
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d", {alpha: true});
  const halo = document.createElement("div");
  const rippleLayer = document.createElement("div");
  const particles = [];
  const pointer = {x: -100, y: -100, targetX: -100, targetY: -100, active: false};
  let frameId = 0;
  let canvasWidth = 0;
  let canvasHeight = 0;
  let lastParticleX = -100;
  let lastParticleY = -100;
  let haloFrameId = 0;

  canvas.className = "sa-interaction-canvas";
  canvas.setAttribute("aria-hidden", "true");
  halo.className = "sa-cursor-halo";
  halo.setAttribute("aria-hidden", "true");
  rippleLayer.className = "sa-ripple-layer";
  rippleLayer.setAttribute("aria-hidden", "true");
  document.body.append(canvas, halo, rippleLayer);

  const resize = () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
    canvasWidth = window.innerWidth;
    canvasHeight = window.innerHeight;
    canvas.width = Math.round(canvasWidth * ratio);
    canvas.height = Math.round(canvasHeight * ratio);
    canvas.style.width = `${canvasWidth}px`;
    canvas.style.height = `${canvasHeight}px`;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  };

  const accentColor = () => getComputedStyle(document.documentElement).getPropertyValue("--accent").trim() || "#38bdf8";

  const keepAnimationAlive = () => {
    if (!frameId) frameId = requestAnimationFrame(render);
  };

  const addParticle = (x, y, burst = false) => {
    if (reducedMotion.matches || particles.length >= maxParticles) return;
    particles.push({
      x: x + (Math.random() - .5) * (burst ? 14 : 8),
      y: y + (Math.random() - .5) * (burst ? 14 : 8),
      vx: (Math.random() - .5) * (burst ? 1.2 : .55),
      vy: (Math.random() - .5) * (burst ? 1.2 : .55) - .15,
      size: Math.random() * (burst ? 2.2 : 1.7) + .8,
      life: burst ? 1 : .82,
      decay: Math.random() * .018 + .014,
      star: Math.random() > .72,
    });
    keepAnimationAlive();
  };

  const addTrail = (x, y) => {
    const distance = Math.hypot(x - lastParticleX, y - lastParticleY);
    if (distance < (touchDevice ? 18 : 10)) return;
    lastParticleX = x;
    lastParticleY = y;
    addParticle(x, y);
    if (!touchDevice && Math.random() > .45) addParticle(x, y);
  };

  const addRipple = (x, y) => {
    if (reducedMotion.matches) return;
    const ripple = document.createElement("span");
    ripple.className = "sa-ripple";
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    rippleLayer.append(ripple);
    ripple.addEventListener("animationend", () => ripple.remove(), {once: true});
    for (let index = 0; index < (mobileBudget ? 2 : 4); index += 1) addParticle(x, y, true);
  };

  const render = () => {
    frameId = 0;
    context.clearRect(0, 0, canvasWidth, canvasHeight);
    context.fillStyle = accentColor();
    particles.forEach((particle) => {
      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.vx *= .985;
      particle.vy = particle.vy * .985 + .008;
      particle.life -= particle.decay;
      context.globalAlpha = Math.max(particle.life, 0) * .7;
      context.beginPath();
      if (particle.star) {
        context.moveTo(particle.x - particle.size * 1.8, particle.y);
        context.lineTo(particle.x + particle.size * 1.8, particle.y);
        context.moveTo(particle.x, particle.y - particle.size * 1.8);
        context.lineTo(particle.x, particle.y + particle.size * 1.8);
        context.strokeStyle = accentColor();
        context.lineWidth = .7;
        context.stroke();
      } else {
        context.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        context.fill();
      }
    });
    context.globalAlpha = 1;
    for (let index = particles.length - 1; index >= 0; index -= 1) {
      if (particles[index].life <= 0) particles.splice(index, 1);
    }
    if (particles.length) keepAnimationAlive();
  };

  const updateHalo = () => {
    haloFrameId = 0;
    if (!pointer.active || !finePointer.matches) return;
    pointer.x += (pointer.targetX - pointer.x) * .16;
    pointer.y += (pointer.targetY - pointer.y) * .16;
    halo.style.transform = `translate3d(${pointer.x}px, ${pointer.y}px, 0) translate3d(-50%, -50%, 0)`;
    if (Math.hypot(pointer.targetX - pointer.x, pointer.targetY - pointer.y) > .2) {
      haloFrameId = requestAnimationFrame(updateHalo);
    }
  };

  const handlePointerMove = (event) => {
    if (event.pointerType === "touch" && reducedMotion.matches) return;
    pointer.targetX = event.clientX;
    pointer.targetY = event.clientY;
    if (finePointer.matches) {
      if (!pointer.active) {
        pointer.active = true;
        halo.classList.add("is-visible");
      }
      if (!haloFrameId) haloFrameId = requestAnimationFrame(updateHalo);
      addTrail(event.clientX, event.clientY);
    } else if (event.pointerType === "touch") {
      addTrail(event.clientX, event.clientY);
    }
  };

  const handlePointerDown = (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    addRipple(event.clientX, event.clientY);
  };

  resize();
  window.addEventListener("resize", resize, {passive: true});
  document.addEventListener("pointermove", handlePointerMove, {passive: true});
  document.addEventListener("pointerdown", handlePointerDown, {passive: true});
  document.addEventListener("pointerleave", () => {
    pointer.active = false;
    halo.classList.remove("is-visible");
  }, {passive: true});

  document.addEventListener("pointerdown", (event) => {
    const target = event.target.closest?.("a, button, [role='button'], .nav-item, .mobile-nav__item, .mobile-menu__link");
    if (target) target.classList.add("sa-fx-target");
  }, {passive: true});

  document.querySelectorAll("a, button, [role='button'], .nav-item, .mobile-nav__item, .mobile-menu__link").forEach((element) => {
    element.classList.add("sa-fx-target");
  });

  reducedMotion.addEventListener?.("change", () => {
    if (reducedMotion.matches) {
      particles.length = 0;
      halo.classList.remove("is-visible");
    }
  });
})();
