// Sticky navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 50) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
});

// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
navToggle?.addEventListener('click', () => {
  navLinks.classList.toggle('open');
});

// Mobile dropdown toggle
document.querySelectorAll('.has-dropdown > a').forEach(link => {
  link.addEventListener('click', function(e) {
    if (window.innerWidth <= 768) {
      e.preventDefault();
      this.parentElement.classList.toggle('open');
    }
  });
});

// Back to top button
const backToTop = document.getElementById('backToTop');
window.addEventListener('scroll', () => {
  if (window.scrollY > 400) backToTop?.classList.add('visible');
  else backToTop?.classList.remove('visible');
});
backToTop?.addEventListener('click', (e) => {
  e.preventDefault();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Auto-dismiss alert messages
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transition = 'opacity 0.5s';
    setTimeout(() => alert.remove(), 500);
  }, 5000);
});





// Video Modal
document.querySelectorAll('.video-thumb').forEach(thumb => {
  thumb.addEventListener('click', () => {
    const videoId = thumb.dataset.video;
    const src = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;
    document.getElementById('videoIframe').src = src;
    document.getElementById('videoModal').classList.add('open');
    document.body.style.overflow = 'hidden';
  });
});

document.getElementById('videoModalClose')?.addEventListener('click', () => {
  document.getElementById('videoIframe').src = '';
  document.getElementById('videoModal').classList.remove('open');
  document.body.style.overflow = '';
});

document.getElementById('videoModal')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) {
    document.getElementById('videoIframe').src = '';
    e.currentTarget.classList.remove('open');
    document.body.style.overflow = '';
  }
});








const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 50) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
});

// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');

navToggle?.addEventListener('click', () => {
  const isOpen = navLinks.classList.toggle('open');
  navToggle.classList.toggle('open', isOpen);
  document.body.style.overflow = isOpen ? 'hidden' : '';
});

// Close nav when clicking outside
document.addEventListener('click', (e) => {
  if (navLinks?.classList.contains('open') &&
      !navLinks.contains(e.target) &&
      !navToggle.contains(e.target)) {
    navLinks.classList.remove('open');
    navToggle.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// Close nav when a link is clicked (non-dropdown)
navLinks?.querySelectorAll('a:not(.has-dropdown > a)').forEach(link => {
  link.addEventListener('click', () => {
    navLinks.classList.remove('open');
    navToggle.classList.remove('open');
    document.body.style.overflow = '';
  });
});

// Mobile dropdown toggle
document.querySelectorAll('.has-dropdown > a').forEach(link => {
  link.addEventListener('click', function(e) {
    if (window.innerWidth <= 768) {
      e.preventDefault();
      const parent = this.parentElement;
      // Close others
      document.querySelectorAll('.has-dropdown.open').forEach(el => {
        if (el !== parent) el.classList.remove('open');
      });
      parent.classList.toggle('open');
    }
  });
});

// Back to top button
const backToTop = document.getElementById('backToTop');
window.addEventListener('scroll', () => {
  if (window.scrollY > 400) backToTop?.classList.add('visible');
  else backToTop?.classList.remove('visible');
});
backToTop?.addEventListener('click', (e) => {
  e.preventDefault();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Auto-dismiss alert messages
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transition = 'opacity 0.5s';
    setTimeout(() => alert.remove(), 500);
  }, 5000);
});

// Gallery Lightbox
document.querySelectorAll('.gallery-item').forEach(item => {
  item.addEventListener('click', () => {
    const img = item.querySelector('img');
    const caption = item.querySelector('.gallery-overlay span');
    document.getElementById('lightboxImg').src = img.src;
    document.getElementById('lightboxImg').alt = img.alt;
    document.getElementById('lightboxCaption').textContent = caption ? caption.textContent : '';
    document.getElementById('lightbox').classList.add('open');
    document.body.style.overflow = 'hidden';
  });
});
document.getElementById('lightboxClose')?.addEventListener('click', () => {
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
});
document.getElementById('lightbox')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) {
    e.currentTarget.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// Video Modal
document.querySelectorAll('.video-thumb').forEach(thumb => {
  thumb.addEventListener('click', () => {
    const videoId = thumb.dataset.video;
    const src = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;
    document.getElementById('videoIframe').src = src;
    document.getElementById('videoModal').classList.add('open');
    document.body.style.overflow = 'hidden';
  });
});
document.getElementById('videoModalClose')?.addEventListener('click', () => {
  document.getElementById('videoIframe').src = '';
  document.getElementById('videoModal').classList.remove('open');
  document.body.style.overflow = '';
});
document.getElementById('videoModal')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) {
    document.getElementById('videoIframe').src = '';
    e.currentTarget.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// FAQ accordion
document.querySelectorAll('.faq-question').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.parentElement;
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item.open').forEach(el => el.classList.remove('open'));
    if (!isOpen) item.classList.add('open');
  });
});
