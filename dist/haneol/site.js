(() => {
  const toggle = document.querySelector('.burger');
  const menu = document.getElementById('haneol-mobile-menu');
  function setMenu(open) {
    menu?.classList.toggle('is-open', open);
    toggle?.setAttribute('aria-expanded', String(open));
    toggle?.setAttribute('aria-label', open ? '메뉴 닫기' : '메뉴 열기');
  }
  toggle?.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') {
      setMenu(false); toggle.focus();
    }
  });
  let noticeTimer;
  document.addEventListener('click', e => {
    if (!(e.target instanceof Element)) return;
    if (!e.target.closest('[data-phone-pending]')) return;
    e.preventDefault();
    let notice = document.querySelector('.haneol-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.className = 'haneol-notice';
      notice.setAttribute('role', 'status');
      document.body.append(notice);
    }
    notice.textContent = '상담 전화번호를 준비 중입니다.';
    clearTimeout(noticeTimer);
    noticeTimer = setTimeout(() => notice.remove(), 4000);
  });
})();
