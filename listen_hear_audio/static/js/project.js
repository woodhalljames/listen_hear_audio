/* Project specific Javascript goes here. */

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
  // Smooth scroll to anchor links
  const anchorLinks = document.querySelectorAll('a[href^="#"]');
  anchorLinks.forEach(link => {
    link.addEventListener('click', function(e) {
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

  // Add to cart with AJAX
  const addToCartForms = document.querySelectorAll('.add-to-cart-form');
  addToCartForms.forEach(form => {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const formData = new FormData(this);
      const url = this.action;
      const button = this.querySelector('button[type="submit"]');
      const originalButtonText = button.innerHTML;
      
      // Disable button and show loading state
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
          // Update cart count badge
          const cartBadge = document.querySelector('.cart-badge');
          if (cartBadge) {
            cartBadge.textContent = data.cart_count;
          } else {
            // Create badge if it doesn't exist
            const cartLink = document.querySelector('a[href*="cart"]');
            if (cartLink && data.cart_count > 0) {
              const badge = document.createElement('span');
              badge.className = 'cart-badge';
              badge.textContent = data.cart_count;
              cartLink.appendChild(badge);
            }
          }
          
          // Show success feedback
          button.innerHTML = '<i class="bi bi-check-circle-fill"></i> Added!';
          button.classList.remove('btn-primary-custom');
          button.classList.add('btn-success');
          
          // Show success notification
          showNotification('Package added to quote!', 'success');
          
          // Reset button after 2 seconds
          setTimeout(() => {
            button.innerHTML = originalButtonText;
            button.classList.remove('btn-success');
            button.classList.add('btn-primary-custom');
            button.disabled = false;
          }, 2000);
        } else {
          // Show error
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

  // Newsletter form (placeholder for now)
  const newsletterForm = document.querySelector('.newsletter-form');
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const email = this.querySelector('input[type="email"]').value;
      if (email) {
        showNotification('Thank you for subscribing!', 'success');
        this.reset();
      }
    });
  }
  
  // Highlight active section in sidebar navigation
  const observerOptions = {
    root: null,
    rootMargin: '-20% 0px -70% 0px',
    threshold: 0
  };
  
  const observerCallback = (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        const navLinks = document.querySelectorAll('.catalog-nav-link');
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${id}`) {
            link.style.backgroundColor = 'var(--white)';
            link.style.color = 'var(--primary-blue)';
          } else {
            link.style.backgroundColor = '';
            link.style.color = '';
          }
        });
      }
    });
  };
  
  const observer = new IntersectionObserver(observerCallback, observerOptions);
  
  // Observe all property type sections
  const sections = document.querySelectorAll('[id^="property-"]');
  sections.forEach(section => observer.observe(section));
});

// Notification helper function
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} alert-dismissible fade show`;
  notification.style.position = 'fixed';
  notification.style.top = '80px';
  notification.style.right = '20px';
  notification.style.zIndex = '9999';
  notification.style.minWidth = '300px';
  notification.style.maxWidth = '400px';
  notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  document.body.appendChild(notification);
  
  // Auto-dismiss after 3 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}