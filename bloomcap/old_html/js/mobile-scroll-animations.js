/**
 * Mobile Scroll Animations - Lightweight scroll observer for mobile
 * Activates animations when elements come into viewport
 */

(function() {
  'use strict';

  // Only run on mobile devices
  if (window.innerWidth > 768) return;

  // Configuration
  const config = {
    threshold: 0.15, // Trigger when 15% of element is visible
    rootMargin: '50px 0px', // Start animation 50px before element enters viewport
    animationClass: 'visible',
    targetSelectors: [
      // Service and advantage blocks
      '.service-area .col-xl-3',
      '.service-area .col-lg-4',
      '.service-area .col-md-6',
      '.service-area .col-sm-6',
      '.widgets-services__single',
      '.single-service',
      '.single-feature',
      
      // Process step cards
      '.process-area .card',
      '.feature-area .card',
      '.card.position-relative',
      
      // Problem cards
      '.problem-card',
      '[style*="border-left"][style*="#ef4444"]',
      
      // Hero content
      '.welcome-content',
      
      // Testimonials
      '.testimonial-card',
      '.quote-box',
      'blockquote',
      
      // CTA sections
      '.cta-section',
      '.cta-area',
      
      // Generic cards
      '.card',
      '.animate-on-scroll'
    ]
  };

  // Create Intersection Observer
  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        // Add visible class with a small delay for smoother experience
        requestAnimationFrame(function() {
          entry.target.classList.add(config.animationClass);
        });
        
        // Stop observing once animated
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: config.threshold,
    rootMargin: config.rootMargin
  });

  // Function to initialize animations
  function initAnimations() {
    // Get all elements to animate
    const elements = document.querySelectorAll(config.targetSelectors.join(', '));
    
    elements.forEach(function(element) {
      // Skip if already visible
      if (element.classList.contains(config.animationClass)) return;
      
      // Check if element is already in viewport
      const rect = element.getBoundingClientRect();
      const isInViewport = rect.top < window.innerHeight && rect.bottom > 0;
      
      if (isInViewport && rect.top < window.innerHeight * 0.85) {
        // Element is already visible, animate immediately
        element.classList.add(config.animationClass);
      } else {
        // Element is not visible, observe it
        observer.observe(element);
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnimations);
  } else {
    initAnimations();
  }

  // Reinitialize on dynamic content load (if using AJAX)
  window.addEventListener('load', initAnimations);

  // Handle orientation change
  let orientationTimer;
  window.addEventListener('orientationchange', function() {
    clearTimeout(orientationTimer);
    orientationTimer = setTimeout(initAnimations, 300);
  });

  // Fallback for older browsers without IntersectionObserver
  if (!window.IntersectionObserver) {
    // Simple fallback: show all elements immediately
    document.addEventListener('DOMContentLoaded', function() {
      const elements = document.querySelectorAll(config.targetSelectors.join(', '));
      elements.forEach(function(element) {
        element.classList.add(config.animationClass);
      });
    });
  }

  // Touch feedback enhancement
  document.addEventListener('touchstart', function(e) {
    const target = e.target.closest('.card, .single-service, .single-feature, .widgets-services__single');
    if (target) {
      target.style.transform = 'scale(0.98)';
    }
  });

  document.addEventListener('touchend', function(e) {
    const target = e.target.closest('.card, .single-service, .single-feature, .widgets-services__single');
    if (target) {
      setTimeout(function() {
        target.style.transform = '';
      }, 100);
    }
  });

})();