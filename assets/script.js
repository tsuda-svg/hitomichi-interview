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
})();
