/* ===================================================================
   HERO MOBILE ENHANCER - Améliorations JavaScript pour mobile
   =================================================================== */

(function() {
    'use strict';
    
    // Détection mobile
    const isMobile = () => window.innerWidth <= 768;
    
    // Optimisations spécifiques mobile
    function initMobileHeroEnhancements() {
        if (!isMobile()) return;
        
        // 1. Ajustement automatique de la hauteur selon la viewport
        adjustHeroHeight();
        
        // 2. Optimisation du scroll smooth
        enableSmoothScrolling();
        
        // 3. Gestion du resize
        window.addEventListener('resize', debounce(adjustHeroHeight, 150));
        
        // 4. Touch feedback amélioré
        enhanceTouchFeedback();
        
        console.log('🎯 Hero mobile optimisé');
    }
    
    // Ajuster la hauteur hero selon la vraie viewport mobile
    function adjustHeroHeight() {
        if (!isMobile()) return;
        
        const welcomeArea = document.querySelector('.welcome-area');
        if (!welcomeArea) return;
        
        // Utiliser la vraie hauteur viewport mobile (sans barre d'adresse)
        const viewportHeight = window.innerHeight;
        const headerHeight = 70; // hauteur du header fixe
        const optimalHeight = Math.max(viewportHeight * 0.65, 400); // minimum 400px
        
        welcomeArea.style.setProperty('min-height', `${optimalHeight}px`, 'important');
        
        // Ajuster le padding-top dynamiquement
        const paddingTop = headerHeight + 16; // 16px de marge
        welcomeArea.style.setProperty('padding-top', `${paddingTop}px`, 'important');
    }
    
    // Smooth scrolling optimisé pour mobile
    function enableSmoothScrolling() {
        const ctaButtons = document.querySelectorAll('a[href="#formulaire"]');
        
        ctaButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const target = document.querySelector('#formulaire');
                if (target) {
                    const headerOffset = 80;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
                    
                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
    
    // Améliorer le feedback tactile
    function enhanceTouchFeedback() {
        const touchElements = document.querySelectorAll('.welcome-content--l3 a, .mobile-menu-trigger');
        
        touchElements.forEach(element => {
            // Touch start feedback
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.95)';
                this.style.transition = 'transform 0.1s ease';
            }, { passive: true });
            
            // Touch end restore
            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                    this.style.transition = '';
                }, 100);
            }, { passive: true });
            
            // Touch cancel restore
            element.addEventListener('touchcancel', function() {
                this.style.transform = '';
                this.style.transition = '';
            }, { passive: true });
        });
    }
    
    // Utility: Debounce function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Gestion de l'orientation mobile
    function handleOrientationChange() {
        if (!isMobile()) return;
        
        // Petit délai pour laisser le navigateur s'adapter
        setTimeout(adjustHeroHeight, 200);
    }
    
    // Initialisation
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initMobileHeroEnhancements);
        } else {
            initMobileHeroEnhancements();
        }
        
        // Écouter les changements d'orientation
        window.addEventListener('orientationchange', handleOrientationChange);
    }
    
    // Démarrer
    init();
    
    // Exposer pour debug
    if (isMobile()) {
        window.heroMobileDebug = {
            adjustHeight: adjustHeroHeight,
            isMobile: isMobile,
            getViewportHeight: () => window.innerHeight
        };
    }
    
})();