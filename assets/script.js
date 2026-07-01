(function () {
  // ---------- Header scroll behavior ----------
  const header = document.querySelector('.site-header');
  if (header) {
    const useLight = header.dataset.headerStyle === 'light';
    const setState = () => {
      const y = window.scrollY;
      if (y > 32) {
        header.classList.add('is-scrolled');
        header.classList.remove('is-light');
      } else {
        header.classList.remove('is-scrolled');
        if (useLight) header.classList.add('is-light');
      }
    };
    setState();
    window.addEventListener('scroll', setState, { passive: true });
  }

  // ---------- Facet tabs ----------
  const tabContainers = document.querySelectorAll('[data-facet]');
  tabContainers.forEach((container) => {
    const tabs = container.querySelectorAll('.facet-tab');
    const panels = container.querySelectorAll('.facet-panel');
    tabs.forEach((tab) => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        const target = tab.dataset.target;
        tabs.forEach((t) => t.setAttribute('data-active', t === tab ? 'true' : 'false'));
        panels.forEach((p) => {
          p.setAttribute('data-active', p.dataset.panel === target ? 'true' : 'false');
        });
      });
    });
  });

  // ---------- Smooth scroll for in-page anchors ----------
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id && id.length > 1) {
        const target = document.querySelector(id);
        if (target) {
          e.preventDefault();
          window.scrollTo({
            top: target.getBoundingClientRect().top + window.scrollY - 80,
            behavior: 'smooth'
          });
        }
      }
    });
  });

  // ---------- Reading progress indicator (circular, bottom-right) ----------
  const article = document.querySelector('article');
  if (article) {
    // インジケーターをbodyに注入（HTMLの改変不要）
    const wrap = document.createElement('div');
    wrap.className = 'reading-progress';
    wrap.setAttribute('aria-hidden', 'true');
    wrap.innerHTML = ''
      + '<svg class="reading-progress-svg" viewBox="0 0 48 48">'
      +   '<circle class="reading-progress-ring" cx="24" cy="24" r="20"/>'
      +   '<circle class="reading-progress-arc" cx="24" cy="24" r="20"/>'
      + '</svg>'
      + '<div class="reading-progress-text">0%</div>';
    document.body.appendChild(wrap);

    const arc = wrap.querySelector('.reading-progress-arc');
    const text = wrap.querySelector('.reading-progress-text');
    const CIRCUMFERENCE = 2 * Math.PI * 20; // r=20
    arc.style.strokeDasharray = CIRCUMFERENCE;
    arc.style.strokeDashoffset = CIRCUMFERENCE;

    const updateProgress = () => {
      const rect = article.getBoundingClientRect();
      const articleTop = rect.top + window.scrollY;
      const articleHeight = article.offsetHeight;
      const viewportH = window.innerHeight;
      const scrolled = Math.max(0, window.scrollY - articleTop + viewportH);
      const total = articleHeight;
      const pct = Math.min(100, Math.max(0, (scrolled / total) * 100));
      arc.style.strokeDashoffset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;
      text.textContent = Math.round(pct) + '%';
      // スクロール200px以上でフェードイン、記事末尾でフェードアウト
      const shouldShow = window.scrollY > 200 && pct < 99.5;
      wrap.classList.toggle('is-visible', shouldShow);
    };
    updateProgress();
    window.addEventListener('scroll', updateProgress, { passive: true });
    window.addEventListener('resize', updateProgress, { passive: true });
  }
})();
