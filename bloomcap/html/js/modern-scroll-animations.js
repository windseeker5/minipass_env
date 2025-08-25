/* ===================================================================
   MODERN SCROLL ANIMATIONS - High Performance Intersection Observer
   Expert-level animation system for benefits & steps sections
   =================================================================== */

class ModernScrollAnimations {
  constructor(options = {}) {
    this.options = {
      // Animation triggers
      rootMargin: '-50px 0px -100px 0px', // Trigger earlier, end later
      threshold: [0, 0.1, 0.3, 0.6, 1],
      
      // Performance
      passive: true,
      once: true, // Animate only once for better performance
      
      // Selectors
      animateSelector: '.animate-on-scroll',
      staggerContainer: '.stagger-container',
      
      // Timing
      staggerDelay: 150,
      
      // Debug
      debug: false,
      
      ...options
    };
    
    this.observer = null;
    this.animatedElements = new Set();
    
    this.init();
  }
  
  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }
  
  setup() {
    // Check for Intersection Observer support
    if (!('IntersectionObserver' in window)) {
      console.warn('IntersectionObserver not supported, falling back to immediate animation');
      this.fallbackAnimation();
      return;
    }
    
    this.createObserver();
    this.observeElements();
    this.setupStaggerContainers();
    
    if (this.options.debug) {
      console.log('🎬 Modern Scroll Animations initialized');
      document.body.classList.add('debug-animations');
    }
  }
  
  createObserver() {
    this.observer = new IntersectionObserver(
      (entries) => this.handleIntersection(entries),
      {
        rootMargin: this.options.rootMargin,
        threshold: this.options.threshold
      }
    );
  }
  
  observeElements() {
    const elements = document.querySelectorAll(this.options.animateSelector);
    
    elements.forEach((element, index) => {
      // Add initial classes for animation
      this.prepareElement(element, index);
      
      // Start observing
      this.observer.observe(element);
    });
    
    if (this.options.debug) {
      console.log(`👀 Observing ${elements.length} elements for animation`);
    }
  }
  
  prepareElement(element, index) {
    // Add modern card class if it's a benefits/steps card
    if (this.isCardElement(element)) {
      element.classList.add('modern-card');
      
      // Find and enhance icons
      const icon = element.querySelector('[class*="fa-"], .icon, i[class*="icon"]');
      if (icon) {
        icon.classList.add('modern-icon');
        
        // Wrap icon in container if needed
        const iconContainer = icon.closest('[style*="background"]') || icon.parentElement;
        if (iconContainer && iconContainer !== element) {
          iconContainer.classList.add('icon-container');
        }
      }
    }
    
    // Enhance titles
    const title = element.querySelector('h1, h2, h3, h4, h5, h6');
    if (title && !title.classList.contains('title-reveal')) {
      title.classList.add('title-reveal');
    }
  }
  
  setupStaggerContainers() {
    const containers = document.querySelectorAll(this.options.staggerContainer);
    
    containers.forEach(container => {
      const children = container.querySelectorAll(this.options.animateSelector);
      
      children.forEach((child, index) => {
        // Add custom delay based on position
        const delay = index * this.options.staggerDelay;
        child.style.setProperty('--stagger-delay', `${delay}ms`);
        child.style.transitionDelay = `${delay}ms`;
      });
    });
  }
  
  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting && entry.intersectionRatio > 0.1) {
        this.animateElement(entry.target);
        
        if (this.options.once) {
          this.observer.unobserve(entry.target);
        }
      }
    });
  }
  
  animateElement(element) {
    // Prevent double animation
    if (this.animatedElements.has(element)) return;
    
    this.animatedElements.add(element);
    
    // Add animation class
    requestAnimationFrame(() => {
      element.classList.add('is-visible');
      
      // Special handling for titles
      const title = element.querySelector('.title-reveal');
      if (title) {
        title.style.animationDelay = '0.2s';
      }
      
      // Fire custom event
      element.dispatchEvent(new CustomEvent('elementAnimated', {
        detail: { element, timestamp: Date.now() }
      }));
      
      if (this.options.debug) {
        console.log('✨ Animated:', element);
      }
    });
  }
  
  isCardElement(element) {
    // Check if element looks like a benefits/steps card
    const cardIndicators = [
      '.widgets__services-single',
      '.single-feature',
      '.single-service',
      '.card',
      '[class*="benefit"]',
      '[class*="step"]'
    ];
    
    return cardIndicators.some(selector => 
      element.matches(selector) || element.closest(selector)
    );
  }
  
  fallbackAnimation() {
    // Immediate animation for unsupported browsers
    const elements = document.querySelectorAll(this.options.animateSelector);
    
    elements.forEach((element, index) => {
      setTimeout(() => {
        element.classList.add('is-visible');
      }, index * this.options.staggerDelay);
    });
  }
  
  // Public methods
  refresh() {
    // Re-observe all elements
    this.observer?.disconnect();
    this.animatedElements.clear();
    this.setup();
  }
  
  destroy() {
    this.observer?.disconnect();
    this.animatedElements.clear();
    
    if (this.options.debug) {
      document.body.classList.remove('debug-animations');
      console.log('💥 Modern Scroll Animations destroyed');
    }
  }
  
  // Utility to manually trigger animation
  animateElementManually(element) {
    if (element && !this.animatedElements.has(element)) {
      this.animateElement(element);
    }
  }
}

// Auto-initialize when DOM is ready
const initModernAnimations = () => {
  // Configuration options
  const config = {
    rootMargin: '-30px 0px -50px 0px',
    staggerDelay: 150,
    debug: true, // ACTIVÉ pour diagnostic
    once: true
  };
  
  // Initialize the animation system
  window.modernAnimations = new ModernScrollAnimations(config);
  
  // Optional: Add to global scope for manual control
  window.animateElement = (selector) => {
    const element = document.querySelector(selector);
    if (element) {
      window.modernAnimations.animateElementManually(element);
    }
  };
  
  console.log('🚀 Modern Scroll Animations ready');
};

// Initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initModernAnimations);
} else {
  initModernAnimations();
}

// Handle page visibility changes for better performance
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    // Pause animations when page is not visible
    document.body.style.setProperty('--anim-duration', '0s');
  } else {
    // Resume animations
    document.body.style.removeProperty('--anim-duration');
  }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModernScrollAnimations;
}