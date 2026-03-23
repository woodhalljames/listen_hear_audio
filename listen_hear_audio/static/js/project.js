/* ══════════════════════════════════════════════════════════════
   Listen Hear! — project.js
   Base utilities + Day/Night homepage engine support
   ══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ── SMOOTH SCROLL ─────────────────────────────────────────
  const anchorLinks = document.querySelectorAll('a[href^="#"]');
  anchorLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });

  // ── ADD TO CART (AJAX) ────────────────────────────────────
  const addToCartForms = document.querySelectorAll('.add-to-cart-form');
  addToCartForms.forEach(form => {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const url = this.action;
      const button = this.querySelector('button[type="submit"]');
      const originalButtonText = button.innerHTML;

      button.disabled = true;
      button.innerHTML = '<i class="bi bi-hourglass-split"></i> Adding...';

      fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        }
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            if (typeof updateCartCount === 'function') {
              updateCartCount(data.cart_count);
            }
            button.innerHTML = '<i class="bi bi-check-circle-fill"></i> Added!';
            button.classList.remove('btn-primary-custom');
            button.classList.add('btn-success');
            showNotification('Package added to quote!', 'success');
            setTimeout(() => {
              button.innerHTML = originalButtonText;
              button.classList.remove('btn-success');
              button.classList.add('btn-primary-custom');
              button.disabled = false;
            }, 2000);
          } else {
            button.innerHTML = originalButtonText;
            button.disabled = false;
            showNotification('Error adding package', 'error');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          button.innerHTML = originalButtonText;
          button.disabled = false;
          showNotification('Error adding package', 'error');
        });
    });
  });


  // ── CATALOG MOBILE DROPDOWN ───────────────────────────────
  const navbarToggler = document.querySelector('.navbar-toggler');
  const isMobileNav = () => navbarToggler && window.getComputedStyle(navbarToggler).display !== 'none';

  document.querySelectorAll('.nav-catalog > a.nav-link').forEach(link => {
    link.addEventListener('click', function (e) {
      if (isMobileNav()) {
        e.preventDefault();
        this.closest('.nav-catalog').classList.toggle('nav-catalog--open');
      }
    });
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.nav-catalog')) {
      document.querySelectorAll('.nav-catalog--open').forEach(el => el.classList.remove('nav-catalog--open'));
    }
  });

  const navbarCollapse = document.getElementById('navbarMain');
  if (navbarCollapse) {
    navbarCollapse.addEventListener('hidden.bs.collapse', function () {
      document.querySelectorAll('.nav-catalog--open').forEach(el => el.classList.remove('nav-catalog--open'));
    });
  }

  // ── CATALOG SIDEBAR NAV HIGHLIGHT ─────────────────────────
  const catNavObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        document.querySelectorAll('.catalog-nav-link').forEach(link => {
          link.style.backgroundColor = '';
          link.style.color = '';
          if (link.getAttribute('href') === `#${id}`) {
            link.style.backgroundColor = 'var(--white)';
            link.style.color = 'var(--primary-blue)';
          }
        });
      }
    });
  }, {
    root: null,
    rootMargin: '-20% 0px -70% 0px',
    threshold: 0
  });

  document.querySelectorAll('[id^="property-"]').forEach(s => catNavObserver.observe(s));


  // ══════════════════════════════════════════════════════════
  //  DAY / NIGHT SCROLL ENGINE (homepage only)
  //  The core color interpolation lives in the inline <script>
  //  block inside home.html for performance (runs before paint).
  //  This section handles complementary UI behaviours:
  //    - Navbar transparency over the hero video
  //    - Navbar restores brand color on scroll
  // ══════════════════════════════════════════════════════════

  const navbar = document.querySelector('.navbar-custom');

  if (navbar && document.querySelector('.lhx-hero')) {

    function updateNavbarOnScroll() {
      const scrollY = window.scrollY;

      if (scrollY < 40) {
        // Fully transparent over hero video
        navbar.style.backgroundColor = 'transparent';
        navbar.style.boxShadow = 'none';
      } else {
        // Fade back to brand blue
        const alpha = Math.min((scrollY - 40) / 120, 1);
        navbar.style.backgroundColor = `rgba(3, 17, 252, ${0.92 + 0.08 * alpha})`;
        navbar.style.boxShadow = `0 2px 20px rgba(0,0,0,${0.15 * alpha})`;
      }
    }

    window.addEventListener('scroll', updateNavbarOnScroll, { passive: true });
    updateNavbarOnScroll();
  }

});


/* ══════════════════════════════════════════════════════════════
   NOTIFICATION HELPER
   ══════════════════════════════════════════════════════════════ */
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} alert-dismissible fade show`;
  Object.assign(notification.style, {
    position: 'fixed',
    top: '80px',
    right: '20px',
    zIndex: '9999',
    minWidth: '300px',
    maxWidth: '400px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
    fontFamily: "'DM Sans', sans-serif",
  });
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}