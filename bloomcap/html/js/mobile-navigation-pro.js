/* ===================================================================
   MOBILE NAVIGATION PRO - JavaScript pour interactions fluides
   =================================================================== */

class MobileNavigationPro {
  constructor() {
    this.isMenuOpen = false;
    this.isMobile = window.innerWidth <= 991;
    this.scrollThreshold = 50;
    this.lastScrollY = 0;
    
    this.init();
  }
  
  init() {
    if (!this.isMobile) return;
    
    this.setupElements();
    this.createMobileElements();
    this.bindEvents();
    this.handleScroll();
    
    console.log('🚀 Navigation mobile PRO initialisée');
  }
  
  setupElements() {
    this.header = document.querySelector('.site-header');
    this.menuTrigger = document.querySelector('.mobile-menu-trigger');
    this.menuBlock = document.querySelector('.menu-block');
    this.menuOverlay = document.querySelector('.menu-overlay');
    this.body = document.body;
    
    // Créer les éléments s'ils n'existent pas
    if (!this.menuOverlay) {
      this.menuOverlay = document.createElement('div');
      this.menuOverlay.className = 'menu-overlay';
      this.body.appendChild(this.menuOverlay);
    }
  }
  
  createMobileElements() {
    // Créer le bouton CTA mobile
    const headerBtn = document.querySelector('.header-btn');
    if (headerBtn && !headerBtn.querySelector('.mobile-cta-btn')) {
      const mobileCTA = document.createElement('a');
      mobileCTA.className = 'mobile-cta-btn';
      mobileCTA.href = '#formulaire';
      mobileCTA.textContent = 'Démarrer';
      mobileCTA.setAttribute('aria-label', 'Commencer maintenant');
      headerBtn.appendChild(mobileCTA);
      
      // Smooth scroll pour le CTA
      mobileCTA.addEventListener('click', this.handleCTAClick.bind(this));
    }
    
    // S'assurer que le hamburger a la bonne structure
    if (this.menuTrigger && !this.menuTrigger.querySelector('span')) {
      this.menuTrigger.innerHTML = '<span></span>';
    }
    
    // Ajouter les attributs d'accessibilité
    if (this.menuTrigger) {
      this.menuTrigger.setAttribute('aria-label', 'Menu principal');
      this.menuTrigger.setAttribute('aria-expanded', 'false');
      this.menuTrigger.setAttribute('role', 'button');
      this.menuTrigger.setAttribute('tabindex', '0');
    }
  }
  
  bindEvents() {
    // Menu toggle
    if (this.menuTrigger) {
      this.menuTrigger.addEventListener('click', this.toggleMenu.bind(this));
      this.menuTrigger.addEventListener('keydown', this.handleKeyDown.bind(this));
    }
    
    // Overlay click
    if (this.menuOverlay) {
      this.menuOverlay.addEventListener('click', this.closeMenu.bind(this));
    }
    
    // Menu links
    const menuLinks = document.querySelectorAll('.site-menu-main a');
    menuLinks.forEach(link => {
      link.addEventListener('click', this.handleMenuLinkClick.bind(this));
    });
    
    // Scroll handler
    window.addEventListener('scroll', this.throttle(this.handleScroll.bind(this), 16));
    
    // Resize handler
    window.addEventListener('resize', this.throttle(this.handleResize.bind(this), 250));
    
    // Escape key
    document.addEventListener('keydown', this.handleEscapeKey.bind(this));
    
    // Touch handlers pour mobile
    this.setupTouchHandlers();
  }
  
  toggleMenu() {
    if (this.isMenuOpen) {
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }
  
  openMenu() {
    if (!this.isMobile) return;
    
    this.isMenuOpen = true;
    
    // Ajouter les classes actives
    this.menuTrigger?.classList.add('is-active');
    this.menuBlock?.classList.add('is-active');
    this.menuOverlay?.classList.add('is-active');
    
    // Bloquer le scroll du body
    this.body.style.overflow = 'hidden';
    this.body.style.position = 'fixed';
    this.body.style.width = '100%';
    this.body.style.top = `-${window.scrollY}px`;
    
    // Accessibility
    this.menuTrigger?.setAttribute('aria-expanded', 'true');
    
    // Focus management
    setTimeout(() => {
      const firstLink = this.menuBlock?.querySelector('.site-menu-main a');
      firstLink?.focus();
    }, 300);
    
    console.log('📱 Menu ouvert');
  }
  
  closeMenu() {
    if (!this.isMenuOpen) return;
    
    this.isMenuOpen = false;
    
    // Retirer les classes actives
    this.menuTrigger?.classList.remove('is-active');
    this.menuBlock?.classList.remove('is-active');
    this.menuOverlay?.classList.remove('is-active');
    
    // Restaurer le scroll
    const scrollY = this.body.style.top;
    this.body.style.overflow = '';
    this.body.style.position = '';
    this.body.style.width = '';
    this.body.style.top = '';
    window.scrollTo(0, parseInt(scrollY || '0') * -1);
    
    // Accessibility
    this.menuTrigger?.setAttribute('aria-expanded', 'false');
    
    // Remettre le focus sur le bouton
    this.menuTrigger?.focus();
    
    console.log('❌ Menu fermé');
  }
  
  handleScroll() {
    const currentScrollY = window.scrollY;
    
    // Effet scroll sur header
    if (this.header) {
      if (currentScrollY > this.scrollThreshold) {
        this.header.classList.add('scrolled');
      } else {
        this.header.classList.remove('scrolled');
      }
    }
    
    // Fermer le menu si scroll important
    if (this.isMenuOpen && Math.abs(currentScrollY - this.lastScrollY) > 100) {
      this.closeMenu();
    }
    
    this.lastScrollY = currentScrollY;
  }
  
  handleResize() {
    const wasMobile = this.isMobile;
    this.isMobile = window.innerWidth <= 991;
    
    // Si on passe de mobile à desktop
    if (wasMobile && !this.isMobile) {
      this.closeMenu();
      this.body.style.overflow = '';
      this.body.style.position = '';
      this.body.style.width = '';
      this.body.style.top = '';
    }
    
    // Si on passe de desktop à mobile
    if (!wasMobile && this.isMobile) {
      this.init();
    }
  }
  
  handleMenuLinkClick(event) {
    const link = event.currentTarget;
    const href = link.getAttribute('href');
    
    // Si c'est un lien interne, fermer le menu
    if (href && href.startsWith('#')) {
      this.closeMenu();
      
      // Smooth scroll vers l'ancre
      const target = document.querySelector(href);
      if (target) {
        event.preventDefault();
        const headerHeight = this.header?.offsetHeight || 60;
        const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;
        
        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    } else {
      // Pour les liens externes, fermer le menu avec un délai
      setTimeout(() => this.closeMenu(), 100);
    }
  }
  
  handleCTAClick(event) {
    event.preventDefault();
    
    const target = document.querySelector('#formulaire');
    if (target) {
      const headerHeight = this.header?.offsetHeight || 60;
      const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;
      
      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    }
  }
  
  handleKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.toggleMenu();
    }
  }
  
  handleEscapeKey(event) {
    if (event.key === 'Escape' && this.isMenuOpen) {
      this.closeMenu();
    }
  }
  
  setupTouchHandlers() {
    // Touch feedback pour les boutons
    const touchElements = [this.menuTrigger, ...document.querySelectorAll('.mobile-cta-btn, .site-menu-main a')];
    
    touchElements.forEach(element => {
      if (!element) return;
      
      element.addEventListener('touchstart', function() {
        this.style.transform = 'scale(0.98)';
        this.style.transition = 'transform 0.1s ease';
      }, { passive: true });
      
      element.addEventListener('touchend', function() {
        setTimeout(() => {
          this.style.transform = '';
          this.style.transition = '';
        }, 100);
      }, { passive: true });
      
      element.addEventListener('touchcancel', function() {
        this.style.transform = '';
        this.style.transition = '';
      }, { passive: true });
    });
  }
  
  // Utility: Throttle function
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
  
  // Public methods pour debug
  getState() {
    return {
      isMenuOpen: this.isMenuOpen,
      isMobile: this.isMobile,
      scrollY: window.scrollY
    };
  }
  
  forceClose() {
    this.closeMenu();
  }
}

// Auto-initialisation
let navigationPro;

function initMobileNavigationPro() {
  // Détruire l'instance précédente si elle existe
  if (navigationPro) {
    navigationPro = null;
  }
  
  // Créer nouvelle instance
  navigationPro = new MobileNavigationPro();
  
  // Exposer pour debug
  window.mobileNavDebug = navigationPro;
}

// Initialiser au chargement
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMobileNavigationPro);
} else {
  initMobileNavigationPro();
}

// Réinitialiser au resize si nécessaire
window.addEventListener('resize', function() {
  if (window.innerWidth <= 991 && !navigationPro) {
    initMobileNavigationPro();
  }
});

// Export pour modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MobileNavigationPro;
}