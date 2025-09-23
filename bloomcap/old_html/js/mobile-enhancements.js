/* ===================================================================
   MOBILE ENHANCEMENTS JAVASCRIPT
   Améliore l'interaction mobile et les performances
   =================================================================== */

(function() {
    'use strict';
    
    // Configuration
    const CONFIG = {
        headerHeight: 70,
        scrollThreshold: 10,
        animationDuration: 300,
        breakpoint: 768
    };
    
    // Variables globales
    let isMenuOpen = false;
    let lastScrollY = 0;
    let ticking = false;
    
    // Elements DOM
    const elements = {
        header: null,
        menuTrigger: null,
        menuBlock: null,
        menuOverlay: null,
        menuClose: null,
        body: document.body
    };
    
    // ============================================================================
    // INITIALISATION
    // ============================================================================
    
    function init() {
        // Attendre le DOM
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeEnhancements);
        } else {
            initializeEnhancements();
        }
    }
    
    function initializeEnhancements() {
        // Récupérer les éléments DOM
        cacheElements();
        
        // Vérifier si on est sur mobile
        if (window.innerWidth <= CONFIG.breakpoint) {
            setupMobileFeatures();
        }
        
        // Écouter les changements de taille d'écran
        window.addEventListener('resize', debounce(handleResize, 250));
        
        console.log('Mobile enhancements initialized');
    }
    
    function cacheElements() {
        elements.header = document.querySelector('.site-header');
        elements.menuTrigger = document.querySelector('.mobile-menu-trigger');
        elements.menuBlock = document.querySelector('.menu-block');
        elements.menuOverlay = document.querySelector('.menu-overlay');
        elements.menuClose = document.querySelector('.mobile-menu-close');
    }
    
    // ============================================================================
    // FONCTIONNALITÉS MOBILE
    // ============================================================================
    
    function setupMobileFeatures() {
        setupHeaderScroll();
        setupMobileMenu();
        setupTouchOptimizations();
        setupFormEnhancements();
        setupAnimationOptimizations();
    }
    
    // Header avec masquage au scroll
    function setupHeaderScroll() {
        if (!elements.header) return;
        
        let isHeaderVisible = true;
        
        function updateHeader() {
            const currentScrollY = window.pageYOffset;
            const isScrollingDown = currentScrollY > lastScrollY;
            const shouldHideHeader = isScrollingDown && currentScrollY > CONFIG.headerHeight && !isMenuOpen;
            
            if (shouldHideHeader && isHeaderVisible) {
                elements.header.classList.add('scrolled-down');
                isHeaderVisible = false;
            } else if (!shouldHideHeader && !isHeaderVisible) {
                elements.header.classList.remove('scrolled-down');
                isHeaderVisible = true;
            }
            
            lastScrollY = currentScrollY;
            ticking = false;
        }
        
        function requestHeaderUpdate() {
            if (!ticking) {
                requestAnimationFrame(updateHeader);
                ticking = true;
            }
        }
        
        window.addEventListener('scroll', requestHeaderUpdate, { passive: true });
    }
    
    // Menu mobile moderne
    function setupMobileMenu() {
        if (!elements.menuTrigger || !elements.menuBlock) return;
        
        // Créer l'overlay s'il n'existe pas
        if (!elements.menuOverlay) {
            elements.menuOverlay = document.createElement('div');
            elements.menuOverlay.className = 'menu-overlay';
            document.body.appendChild(elements.menuOverlay);
        }
        
        // Event listeners
        elements.menuTrigger.addEventListener('click', toggleMenu);
        elements.menuOverlay.addEventListener('click', closeMenu);
        
        if (elements.menuClose) {
            elements.menuClose.addEventListener('click', closeMenu);
        }
        
        // Fermer le menu avec Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && isMenuOpen) {
                closeMenu();
            }
        });
        
        // Fermer le menu lors du clic sur un lien
        const menuLinks = elements.menuBlock.querySelectorAll('a');
        menuLinks.forEach(link => {
            link.addEventListener('click', closeMenu);
        });
    }
    
    function toggleMenu() {
        if (isMenuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    function openMenu() {
        isMenuOpen = true;
        elements.menuTrigger.classList.add('is-active');
        elements.menuBlock.classList.add('is-active');
        elements.menuOverlay.classList.add('is-active');
        elements.body.style.overflow = 'hidden';
        
        // Focus management
        const firstFocusable = elements.menuBlock.querySelector('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            setTimeout(() => firstFocusable.focus(), CONFIG.animationDuration);
        }
    }
    
    function closeMenu() {
        isMenuOpen = false;
        elements.menuTrigger.classList.remove('is-active');
        elements.menuBlock.classList.remove('is-active');
        elements.menuOverlay.classList.remove('is-active');
        elements.body.style.overflow = '';
        
        // Retourner le focus au trigger
        elements.menuTrigger.focus();
    }
    
    // Optimisations tactiles
    function setupTouchOptimizations() {
        // Améliorer les interactions tactiles sur les boutons
        const touchElements = document.querySelectorAll('.btn, button, a[class*="btn"]');
        
        touchElements.forEach(element => {
            element.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
            }, { passive: true });
            
            element.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            }, { passive: true });
        });
        
        // Prévenir le zoom accidentel sur les inputs
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                const viewport = document.querySelector('meta[name="viewport"]');
                if (viewport) {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no');
                }
            });
            
            input.addEventListener('blur', function() {
                const viewport = document.querySelector('meta[name="viewport"]');
                if (viewport) {
                    viewport.setAttribute('content', 'width=device-width, initial-scale=1');
                }
            });
        });
    }
    
    // Améliorations des formulaires
    function setupFormEnhancements() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Animation de focus sur les champs
            const formControls = form.querySelectorAll('.form-control, .form-select');
            
            formControls.forEach(control => {
                control.addEventListener('focus', function() {
                    this.parentElement.classList.add('focused');
                });
                
                control.addEventListener('blur', function() {
                    this.parentElement.classList.remove('focused');
                    if (this.value.trim() !== '') {
                        this.parentElement.classList.add('filled');
                    } else {
                        this.parentElement.classList.remove('filled');
                    }
                });
            });
            
            // Validation en temps réel
            form.addEventListener('input', function(e) {
                if (e.target.matches('input[type="email"]')) {
                    validateEmail(e.target);
                } else if (e.target.matches('input[type="tel"]')) {
                    validatePhone(e.target);
                }
            });
        });
    }
    
    function validateEmail(input) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isValid = emailRegex.test(input.value);
        
        input.classList.toggle('is-invalid', !isValid && input.value !== '');
        input.classList.toggle('is-valid', isValid);
    }
    
    function validatePhone(input) {
        const phoneRegex = /^[\+]?[\d\s\-\(\)]{10,}$/;
        const isValid = phoneRegex.test(input.value);
        
        input.classList.toggle('is-invalid', !isValid && input.value !== '');
        input.classList.toggle('is-valid', isValid);
    }
    
    // Optimisations des animations
    function setupAnimationOptimizations() {
        // Désactiver les animations si l'utilisateur préfère
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.style.setProperty('--mobile-transition', 'none');
            return;
        }
        
        // Optimiser AOS pour mobile
        if (typeof AOS !== 'undefined') {
            AOS.init({
                duration: 400,
                easing: 'ease-out',
                once: true,
                offset: 50,
                disable: function() {
                    return window.innerWidth < 768;
                }
            });
        }
        
        // Intersection Observer pour les animations légères
        if ('IntersectionObserver' in window) {
            setupScrollAnimations();
        }
    }
    
    function setupScrollAnimations() {
        const animatedElements = document.querySelectorAll('.card, .widgets, .single-feature');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        animatedElements.forEach(element => {
            element.style.animationPlayState = 'paused';
            observer.observe(element);
        });
    }
    
    // ============================================================================
    // GESTION DES ÉVÉNEMENTS
    // ============================================================================
    
    function handleResize() {
        const isMobile = window.innerWidth <= CONFIG.breakpoint;
        
        if (isMobile && !document.body.classList.contains('mobile-optimized')) {
            document.body.classList.add('mobile-optimized');
            setupMobileFeatures();
        } else if (!isMobile && document.body.classList.contains('mobile-optimized')) {
            document.body.classList.remove('mobile-optimized');
            // Nettoyer les modifications mobile
            if (isMenuOpen) {
                closeMenu();
            }
        }
        
        // Recalculer la hauteur du viewport pour mobile
        if (isMobile) {
            updateViewportHeight();
        }
    }
    
    function updateViewportHeight() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
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
    
    // Détection du support tactile
    function isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    // ============================================================================
    // AMÉLIORATION DES PERFORMANCES
    // ============================================================================
    
    // Lazy loading des images si pas déjà géré
    function setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const images = document.querySelectorAll('img[data-src]');
            
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            images.forEach(img => imageObserver.observe(img));
        }
    }
    
    // Préchargement des ressources critiques
    function preloadCriticalResources() {
        const criticalImages = [
            '/image/home-3/welcome-woman-l3.png'
        ];
        
        criticalImages.forEach(src => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = src;
            document.head.appendChild(link);
        });
    }
    
    // ============================================================================
    // ACCESSIBILITÉ
    // ============================================================================
    
    function setupAccessibility() {
        // Améliorer la navigation au clavier
        const focusableElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        
        focusableElements.forEach(element => {
            element.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    if (this.tagName === 'A' || this.tagName === 'BUTTON') {
                        e.preventDefault();
                        this.click();
                    }
                }
            });
        });
        
        // Annoncer les changements d'état aux lecteurs d'écran
        if (elements.menuTrigger) {
            elements.menuTrigger.setAttribute('aria-expanded', 'false');
            elements.menuTrigger.setAttribute('aria-controls', 'mobile-menu');
            elements.menuTrigger.setAttribute('aria-label', 'Ouvrir le menu de navigation');
        }
        
        if (elements.menuBlock) {
            elements.menuBlock.setAttribute('id', 'mobile-menu');
            elements.menuBlock.setAttribute('aria-hidden', 'true');
        }
    }
    
    // ============================================================================
    // INITIALISATION
    // ============================================================================
    
    // Démarrer l'initialisation
    init();
    
    // Configurer l'accessibilité
    setupAccessibility();
    
    // Configurer le lazy loading
    setupLazyLoading();
    
    // Précharger les ressources critiques
    preloadCriticalResources();
    
    // Exposer certaines fonctions pour debug
    window.MobileEnhancements = {
        toggleMenu,
        closeMenu,
        updateViewportHeight
    };
    
})();