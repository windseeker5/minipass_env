/* ===================================================================
   MOBILE FIX JAVASCRIPT - Gestion interactions mobile
   Améliore le comportement du menu et des animations
   =================================================================== */

(function() {
    'use strict';
    
    let isMobile = window.innerWidth <= 768;
    let menuOpen = false;
    
    // Initialisation
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initMobileFix);
        } else {
            initMobileFix();
        }
    }
    
    function initMobileFix() {
        if (isMobile) {
            setupMobileMenu();
            setupMobileAnimations();
            setupTouchInteractions();
        }
        
        window.addEventListener('resize', debounce(handleResize, 250));
    }
    
    // ============================================================================
    // MENU MOBILE
    // ============================================================================
    
    function setupMobileMenu() {
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        const menuClose = document.querySelector('.mobile-menu-close');
        
        if (!menuTrigger || !menuBlock) return;
        
        // Créer l'overlay s'il n'existe pas
        if (!menuOverlay) {
            const overlay = document.createElement('div');
            overlay.className = 'menu-overlay';
            document.body.appendChild(overlay);
        }
        
        // Event listeners
        menuTrigger.addEventListener('click', toggleMobileMenu);
        
        if (menuOverlay) {
            menuOverlay.addEventListener('click', closeMobileMenu);
        }
        
        if (menuClose) {
            menuClose.addEventListener('click', closeMobileMenu);
        }
        
        // Fermer avec Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && menuOpen) {
                closeMobileMenu();
            }
        });
        
        // Fermer lors du clic sur un lien
        const menuLinks = menuBlock.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', closeMobileMenu);
        });
    }
    
    function toggleMobileMenu() {
        if (menuOpen) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    }
    
    function openMobileMenu() {
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        
        if (!menuBlock) return;
        
        menuOpen = true;
        menuBlock.classList.add('is-active');
        
        if (menuOverlay) {
            menuOverlay.classList.add('is-active');
        }
        
        if (menuTrigger) {
            menuTrigger.classList.add('is-active');
        }
        
        // Bloquer le scroll du body
        document.body.style.overflow = 'hidden';
        
        // Focus management
        const firstLink = menuBlock.querySelector('a');
        if (firstLink) {
            setTimeout(() => firstLink.focus(), 300);
        }
    }
    
    function closeMobileMenu() {
        const menuBlock = document.querySelector('.menu-block');
        const menuOverlay = document.querySelector('.menu-overlay');
        const menuTrigger = document.querySelector('.mobile-menu-trigger');
        
        if (!menuBlock) return;
        
        menuOpen = false;
        menuBlock.classList.remove('is-active');
        
        if (menuOverlay) {
            menuOverlay.classList.remove('is-active');
        }
        
        if (menuTrigger) {
            menuTrigger.classList.remove('is-active');
        }
        
        // Rétablir le scroll
        document.body.style.overflow = '';
        
        // Retourner le focus au trigger
        if (menuTrigger) {
            menuTrigger.focus();
        }
    }
    
    // ============================================================================
    // ANIMATIONS MOBILES
    // ============================================================================
    
    function setupMobileAnimations() {
        // Vérifier si les animations sont désactivées par l'utilisateur
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            // Désactiver les animations
            const style = document.createElement('style');
            style.textContent = `
                @media screen and (max-width: 768px) {
                    .welcome-content--l3 > *,
                    .welcome-area .col-lg-5 {
                        opacity: 1 !important;
                        transform: none !important;
                        animation: none !important;
                    }
                }
            `;
            document.head.appendChild(style);
            return;
        }
        
        // Observer pour déclencher les animations au scroll
        if ('IntersectionObserver' in window) {
            setupScrollAnimations();
        }
    }
    
    function setupScrollAnimations() {
        const heroContent = document.querySelector('.welcome-content--l3');
        
        if (!heroContent) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && entry.intersectionRatio > 0.3) {
                    // Les animations CSS prennent le relais
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.3,
            rootMargin: '0px 0px -50px 0px'
        });
        
        observer.observe(heroContent);
    }
    
    // ============================================================================
    // INTERACTIONS TACTILES
    // ============================================================================
    
    function setupTouchInteractions() {
        // Améliorer les interactions tactiles sur les boutons
        const touchElements = document.querySelectorAll('.btn, button, a[class*="btn"], .mobile-menu-trigger');
        
        touchElements.forEach(element => {
            // Effet de pression tactile
            element.addEventListener('touchstart', function() {
                this.style.opacity = '0.8';
                this.style.transform = 'scale(0.98)';
            }, { passive: true });
            
            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.opacity = '';
                    this.style.transform = '';
                }, 150);
            }, { passive: true });
            
            element.addEventListener('touchcancel', function() {
                this.style.opacity = '';
                this.style.transform = '';
            }, { passive: true });
        });
        
        // Optimisation du scroll tactile
        const welcomeArea = document.querySelector('.welcome-area');
        if (welcomeArea) {
            welcomeArea.style.webkitOverflowScrolling = 'touch';
        }
    }
    
    // ============================================================================
    // GESTION RESPONSIVE
    // ============================================================================
    
    function handleResize() {
        const wasMobile = isMobile;
        isMobile = window.innerWidth <= 768;
        
        // Si on passe de mobile à desktop ou vice versa
        if (wasMobile !== isMobile) {
            if (menuOpen && !isMobile) {
                // Fermer le menu si on passe en desktop
                closeMobileMenu();
            }
            
            if (isMobile && !wasMobile) {
                // Réinitialiser pour mobile
                setupMobileMenu();
                setupMobileAnimations();
                setupTouchInteractions();
            }
        }
        
        // Recalculer la hauteur du viewport
        updateViewportHeight();
    }
    
    function updateViewportHeight() {
        if (isMobile) {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        }
    }
    
    // ============================================================================
    // OPTIMISATIONS
    // ============================================================================
    
    function optimizeForMobile() {
        // Précharger les ressources critiques
        const criticalImages = document.querySelectorAll('.welcome-area img');
        criticalImages.forEach(img => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = img.src;
            document.head.appendChild(link);
        });
        
        // Désactiver les animations coûteuses si appareil lent
        if (isLowEndDevice()) {
            document.documentElement.style.setProperty('--animation-duration', '0.2s');
        }
    }
    
    function isLowEndDevice() {
        return navigator.hardwareConcurrency < 4 || 
               navigator.deviceMemory < 4 ||
               /Android.*[4-6]\./.test(navigator.userAgent);
    }
    
    // ============================================================================
    // UTILITAIRES
    // ============================================================================
    
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
    
    function isTouchDevice() {
        return 'ontouchstart' in window || 
               navigator.maxTouchPoints > 0;
    }
    
    // ============================================================================
    // INITIALISATION
    // ============================================================================
    
    // Démarrer l'initialisation
    init();
    
    // Optimisations supplémentaires
    if (isMobile) {
        optimizeForMobile();
        updateViewportHeight();
    }
    
    // Exposer pour debug
    window.MobileFix = {
        toggleMobileMenu,
        closeMobileMenu,
        isMobile: () => isMobile,
        menuOpen: () => menuOpen
    };
    
})();