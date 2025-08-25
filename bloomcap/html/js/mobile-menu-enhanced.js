/* ===================================================================
   MOBILE MENU ENHANCED - JavaScript avec animations fluides
   =================================================================== */

(function() {
    'use strict';
    
    // Variables globales
    let isMenuOpen = false;
    let isMobile = false;
    let scrollY = 0;
    
    // Éléments DOM
    let menuTrigger, menuBlock, menuOverlay, header, body;
    
    // Vérifier si on est sur mobile
    function checkMobile() {
        isMobile = window.innerWidth <= 991;
    }
    
    // Initialiser seulement sur mobile
    function init() {
        checkMobile();
        
        if (!isMobile) return;
        
        setupElements();
        createOverlay();
        bindEvents();
        closeMenu(); // S'assurer que le menu est fermé au démarrage
        
        console.log('🎨 Menu mobile enhanced initialisé');
    }
    
    function setupElements() {
        menuTrigger = document.querySelector('.mobile-menu-trigger');
        menuBlock = document.querySelector('.menu-block');
        menuOverlay = document.querySelector('.menu-overlay');
        header = document.querySelector('.site-header');
        body = document.body;
        
        // Ajouter les attributs d'accessibilité
        if (menuTrigger) {
            menuTrigger.setAttribute('aria-label', 'Menu principal');
            menuTrigger.setAttribute('aria-expanded', 'false');
            menuTrigger.setAttribute('type', 'button');
            menuTrigger.setAttribute('role', 'button');
        }
    }
    
    function createOverlay() {
        if (!menuOverlay && menuBlock) {
            menuOverlay = document.createElement('div');
            menuOverlay.className = 'menu-overlay';
            body.appendChild(menuOverlay);
        }
    }
    
    function bindEvents() {
        // Click sur hamburger
        if (menuTrigger) {
            menuTrigger.addEventListener('click', toggleMenu);
            menuTrigger.addEventListener('keydown', handleKeyDown);
        }
        
        // Click sur overlay
        if (menuOverlay) {
            menuOverlay.addEventListener('click', closeMenu);
        }
        
        // Liens du menu avec smooth scroll
        const menuLinks = document.querySelectorAll('.site-menu-main a');
        menuLinks.forEach(link => {
            link.addEventListener('click', handleMenuLinkClick);
        });
        
        // Scroll pour header effect
        window.addEventListener('scroll', handleScroll, { passive: true });
        
        // Resize
        window.addEventListener('resize', handleResize);
        
        // Escape key
        document.addEventListener('keydown', handleEscapeKey);
        
        // Touch events pour feedback tactile
        setupTouchFeedback();
    }
    
    function toggleMenu() {
        if (isMenuOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    function openMenu() {
        if (!isMobile || isMenuOpen) return;
        
        isMenuOpen = true;
        scrollY = window.scrollY;
        
        // Ajouter les classes actives
        if (menuTrigger) menuTrigger.classList.add('is-active');
        if (menuBlock) menuBlock.classList.add('is-active');
        if (menuOverlay) menuOverlay.classList.add('is-active');
        
        // Bloquer le scroll du body
        body.style.overflow = 'hidden';
        body.style.position = 'fixed';
        body.style.width = '100%';
        body.style.top = `-${scrollY}px`;
        
        // ARIA
        if (menuTrigger) menuTrigger.setAttribute('aria-expanded', 'true');
        
        // Focus sur premier lien après animation
        setTimeout(() => {
            const firstLink = menuBlock?.querySelector('.site-menu-main a');
            if (firstLink) firstLink.focus();
        }, 400);
        
        // Haptic feedback sur mobile
        if ('vibrate' in navigator) {
            navigator.vibrate(50);
        }
    }
    
    function closeMenu() {
        if (!isMenuOpen) return;
        
        isMenuOpen = false;
        
        // Retirer les classes actives
        if (menuTrigger) menuTrigger.classList.remove('is-active');
        if (menuBlock) menuBlock.classList.remove('is-active');
        if (menuOverlay) menuOverlay.classList.remove('is-active');
        
        // Restaurer le scroll
        body.style.overflow = '';
        body.style.position = '';
        body.style.width = '';
        body.style.top = '';
        
        // Restaurer la position de scroll
        if (scrollY) {
            window.scrollTo(0, scrollY);
        }
        
        // ARIA
        if (menuTrigger) menuTrigger.setAttribute('aria-expanded', 'false');
        
        // Remettre le focus sur hamburger
        setTimeout(() => {
            if (menuTrigger) menuTrigger.focus();
        }, 100);
    }
    
    function handleMenuLinkClick(event) {
        const link = event.currentTarget;
        const href = link.getAttribute('href');
        
        // Animation de click
        link.style.transform = 'scale(0.95)';
        setTimeout(() => {
            link.style.transform = '';
        }, 150);
        
        // Si c'est un lien interne (#), fermer le menu et faire smooth scroll
        if (href && href.startsWith('#')) {
            event.preventDefault();
            closeMenu();
            
            const target = document.querySelector(href);
            if (target) {
                setTimeout(() => {
                    const headerHeight = header?.offsetHeight || 64;
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }, 100);
            }
        } else {
            // Pour les liens externes, fermer le menu avec délai
            setTimeout(closeMenu, 150);
        }
    }
    
    function handleScroll() {
        if (!isMobile || !header) return;
        
        const currentScrollY = window.scrollY;
        
        // Effet scroll sur header
        if (currentScrollY > 20) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        // Fermer le menu si scroll important
        if (isMenuOpen && Math.abs(currentScrollY - scrollY) > 100) {
            closeMenu();
        }
    }
    
    function handleResize() {
        const wasMobile = isMobile;
        checkMobile();
        
        // Si on passe de mobile à desktop
        if (wasMobile && !isMobile && isMenuOpen) {
            closeMenu();
            // Nettoyer les styles body
            body.style.overflow = '';
            body.style.position = '';
            body.style.width = '';
            body.style.top = '';
        }
        
        // Si on passe de desktop à mobile, réinitialiser
        if (!wasMobile && isMobile) {
            setTimeout(init, 100);
        }
    }
    
    function handleKeyDown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            toggleMenu();
        }
    }
    
    function handleEscapeKey(event) {
        if (event.key === 'Escape' && isMenuOpen) {
            closeMenu();
        }
    }
    
    function setupTouchFeedback() {
        // Touch feedback pour le hamburger
        if (menuTrigger) {
            menuTrigger.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.95)';
            }, { passive: true });
            
            menuTrigger.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                }, 100);
            }, { passive: true });
            
            menuTrigger.addEventListener('touchcancel', function() {
                this.style.transform = '';
            }, { passive: true });
        }
        
        // Touch feedback pour les liens de menu
        const menuLinks = document.querySelectorAll('.site-menu-main a');
        menuLinks.forEach(link => {
            link.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98) translateX(2px)';
                this.style.transition = 'transform 0.1s ease';
            }, { passive: true });
            
            link.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                    this.style.transition = '';
                }, 100);
            }, { passive: true });
            
            link.addEventListener('touchcancel', function() {
                this.style.transform = '';
                this.style.transition = '';
            }, { passive: true });
        });
    }
    
    // Gestion de l'orientation
    function handleOrientationChange() {
        if (isMenuOpen) {
            closeMenu();
        }
        setTimeout(() => {
            checkMobile();
            if (isMobile) {
                init();
            }
        }, 200);
    }
    
    // Initialisation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Event listeners globaux
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // API publique pour debug et contrôle externe
    window.mobileMenuEnhanced = {
        toggle: toggleMenu,
        open: openMenu,
        close: closeMenu,
        isOpen: () => isMenuOpen,
        isMobile: () => isMobile,
        reinit: init
    };
    
})();