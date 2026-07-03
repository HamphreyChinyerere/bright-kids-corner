// Particle system (vanilla JS) - app static copy
console.log('[particles] particle-system.js loaded');
(()=>{
  const MAX_ACTIVE = 20; // strict maximum
  let activeCount = 0; // live counter
  const neonClasses = ['neon-red','neon-green','neon-pink','black','neon-purple','neon-blue','neon-orange','neon-yellow'];
  const spawnMinMs = 250;
  const spawnMaxMs = 900;
  const lingerMin = 1000; // ms
  const lingerMax = 4000; // ms

  function randBetween(a,b){ return Math.random()*(b-a)+a }
  function choose(arr){ return arr[Math.floor(Math.random()*arr.length)] }

  const terms = [];
  if (typeof particleTerms === 'object'){
    for (const k of Object.keys(particleTerms)){
      for (const t of particleTerms[k]) terms.push(t);
    }
  }

  function createContainer(){
    let c = document.createElement('div');
    c.className = 'particle-container';
    c.style.zIndex = '1';
    c.style.pointerEvents = 'none';
    document.body.appendChild(c);
    return c;
  }

  function withinViewportAvoidCenter(xPct,yPct,centerRect){
    const vw = window.innerWidth; const vh = window.innerHeight;
    const x = xPct*vw; const y = yPct*vh;
    if (!centerRect) return {x,y};
    let nx = x, ny = y;
    if (nx >= centerRect.left && nx <= centerRect.right && ny >= centerRect.top && ny <= centerRect.bottom){
      if (nx - centerRect.left < centerRect.right - nx) nx = centerRect.left - 30;
      else nx = centerRect.right + 30;
      if (ny < centerRect.top) ny = centerRect.top - 30;
      if (ny > centerRect.bottom) ny = centerRect.bottom + 30;
    }
    return {x:nx,y:ny};
  }

  function getAuthCardRect(){
    const el = document.getElementById('auth-card');
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
  }

  function spawnParticle(container, centerRect){
    if (activeCount >= MAX_ACTIVE) return;
    if (!terms.length) return;
    activeCount++;

    const p = document.createElement('div');
    p.className = 'particle ' + choose(neonClasses);
    p.textContent = choose(terms);
    p.style.fontSize = Math.floor(randBetween(14,26)) + 'px';

    const xPct = Math.random();
    const yPct = Math.random();
    const pos = withinViewportAvoidCenter(xPct,yPct, centerRect);
    p.style.left = pos.x + 'px';
    p.style.top = pos.y + 'px';

    let lifespan = Math.floor(randBetween(lingerMin, lingerMax));
    let removed = false;

    function beginFade(){
      if (removed) return;
      p.classList.add('particle-fade');
      const to = setTimeout(()=>{
        if (removed) return;
        removed = true;
        activeCount--;
        p.remove();
      }, 300);
    }

    let remaining = lifespan;
    let countdownTimer = null;
    let startTime = Date.now();

    function startCountdown(){
      startTime = Date.now();
      countdownTimer = setTimeout(()=>{
        beginFade();
      }, remaining);
    }

    function pauseCountdown(){
      if (!countdownTimer) return;
      clearTimeout(countdownTimer);
      countdownTimer = null;
      const elapsed = Date.now() - startTime;
      remaining = Math.max(0, remaining - elapsed);
    }

    p.addEventListener('mouseenter', function(){
      p.style.transition = 'transform 120ms linear, opacity 120ms linear';
      p.style.transform = 'translate(-50%, -50%) scale(1.4)';
      pauseCountdown();
    });
    p.addEventListener('mouseleave', function(){
      p.style.transition = '';
      p.style.transform = 'translate(-50%, -50%) scale(1)';
      if (remaining < 150) remaining = 250;
      startCountdown();
    });

    p.style.pointerEvents = 'auto';

    container.appendChild(p);
    startCountdown();
  }

  function init(){
    const container = createContainer();
    const centerRect = getAuthCardRect();

    const auth = document.querySelector('.bg-white.rounded-2xl.p-10');
    if (auth && !document.getElementById('auth-card')){
      auth.id = 'auth-card';
      auth.style.position = 'relative';
      auth.style.zIndex = '5';
    }

    (function loop(){
      const wait = Math.floor(randBetween(spawnMinMs, spawnMaxMs));
      setTimeout(()=>{
        spawnParticle(container, centerRect);
        loop();
      }, wait);
    })();
  }

  document.addEventListener('DOMContentLoaded', function(){
    if (document.querySelector('form')){
      init();
    }
  });

})();
