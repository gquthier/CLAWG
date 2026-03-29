/* ═══════════════════════════════════════════════
   SMART-CLAWG — Animations & Interactions
   ═══════════════════════════════════════════════ */

// ─── NEURAL PARTICLE CANVAS ───
(function initNeural() {
  const canvas = document.getElementById("neural-bg");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let w, h, particles, mouse = { x: -1000, y: -1000 };
  const PARTICLE_COUNT = 80;
  const CONNECT_DIST = 140;
  const MOUSE_DIST = 200;

  function resize() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function createParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 1.8 + 0.6,
        pulse: Math.random() * Math.PI * 2,
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);

    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      const a = particles[i];
      for (let j = i + 1; j < particles.length; j++) {
        const b = particles[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECT_DIST) {
          const alpha = (1 - dist / CONNECT_DIST) * 0.15;
          ctx.strokeStyle = `rgba(155,93,229,${alpha})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }

      // Mouse connection
      const mx = a.x - mouse.x;
      const my = a.y - mouse.y;
      const md = Math.sqrt(mx * mx + my * my);
      if (md < MOUSE_DIST) {
        const alpha = (1 - md / MOUSE_DIST) * 0.3;
        ctx.strokeStyle = `rgba(196,161,246,${alpha})`;
        ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(mouse.x, mouse.y);
        ctx.stroke();
      }
    }

    // Draw particles
    for (const p of particles) {
      p.pulse += 0.02;
      const glow = 0.4 + Math.sin(p.pulse) * 0.25;
      ctx.fillStyle = `rgba(155,93,229,${glow})`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();

      // Move
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
    }

    requestAnimationFrame(draw);
  }

  window.addEventListener("resize", () => { resize(); createParticles(); });
  document.addEventListener("mousemove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; });

  resize();
  createParticles();
  draw();
})();

// ─── CURSOR GLOW FOLLOWER ───
(function initCursorGlow() {
  const glow = document.getElementById("cursor-glow");
  if (!glow) return;
  let gx = 0, gy = 0, cx = 0, cy = 0;

  document.addEventListener("mousemove", (e) => {
    gx = e.clientX;
    gy = e.clientY;
  });

  function animate() {
    cx += (gx - cx) * 0.08;
    cy += (gy - cy) * 0.08;
    glow.style.left = cx + "px";
    glow.style.top = cy + "px";
    requestAnimationFrame(animate);
  }
  animate();
})();

// ─── TERMINAL TYPING ANIMATION ───
(function initTerminal() {
  const terminal = document.getElementById("terminal");
  if (!terminal) return;

  const lines = terminal.querySelectorAll(".terminal-line");
  let started = false;

  function runTerminal() {
    if (started) return;
    started = true;

    lines.forEach((line) => {
      const delay = parseInt(line.dataset.delay || "0", 10);
      const cmd = line.querySelector(".cmd");

      setTimeout(() => {
        line.classList.add("visible");

        if (cmd) {
          const fullText = cmd.dataset.text || "";
          let i = 0;
          cmd.textContent = "";
          const interval = setInterval(() => {
            cmd.textContent += fullText[i];
            i++;
            if (i >= fullText.length) {
              clearInterval(interval);
              cmd.classList.add("done");
            }
          }, 28);
        }
      }, delay);
    });
  }

  // Start when terminal is in view
  const obs = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      runTerminal();
      obs.disconnect();
    }
  }, { threshold: 0.3 });
  obs.observe(terminal);
})();

// ─── SCROLL REVEAL ───
(function initReveal() {
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -30px 0px" }
  );
  document.querySelectorAll(".reveal-up").forEach((el) => obs.observe(el));
})();

// ─── MOBILE MENU ───
(function initMenu() {
  const btn = document.getElementById("menu-btn");
  const links = document.getElementById("nav-links");
  if (!btn || !links) return;

  btn.addEventListener("click", () => {
    links.classList.toggle("open");
  });

  links.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => links.classList.remove("open"));
  });
})();

// ─── COPY BUTTONS ───
(function initCopy() {
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.copy;
      const code = id ? document.getElementById(id) : null;
      if (!code) return;

      try {
        await navigator.clipboard.writeText(code.textContent || "");
        btn.classList.add("copied");
        setTimeout(() => btn.classList.remove("copied"), 1500);
      } catch { /* noop */ }
    });
  });
})();

// ─── NAV SHRINK ON SCROLL ───
(function initNavScroll() {
  const nav = document.querySelector(".nav-wrap");
  if (!nav) return;
  let ticking = false;

  window.addEventListener("scroll", () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        nav.style.borderBottomColor = window.scrollY > 60
          ? "rgba(155,93,229,.22)"
          : "rgba(155,93,229,.14)";
        ticking = false;
      });
      ticking = true;
    }
  });
})();

// ─── VAULT NODE STAGGER ANIMATION ───
(function initVaultPulse() {
  const nodes = document.querySelectorAll("[data-pulse]");
  nodes.forEach((node, i) => {
    node.style.animationDelay = `${i * 0.12}s`;
  });
})();
