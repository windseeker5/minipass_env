/* ===================================================================
   MOBILE MENU SIMPLE - JavaScript fiable et léger
   =================================================================== */

(function() {
    'use strict';
    
    // Variables
    let isMenuOpen = false;
    let scrollY = 0;
    
    // Éléments DOM
    let menuTrigger, menuBlock, menuOverlay, header, body;
    
    // Vérifier si on est sur mobile
    function isMobile() {
        return window.innerWidth <= 991;
    }
    
    // Initialiser
    function init() {
        if (!isMobile()) return;
        
        setupElements();
        createOverlay();
        bindEvents();
        closeMenu(); // S'assurer que le menu est fermé
        
        console.log('📱 Menu mobile simple initialisé');
    }
    
    function setupElements() {
        menuTrigger = document.querySelector('.mobile-menu-trigger');
        menuBlock = document.querySelector('.menu-block');
        menuOverlay = document.querySelector('.menu-overlay');
        header = document.querySelector('.site-header');
        body = document.body;
        
        // ARIA attributes
        if (menuTrigger) {
            menuTrigger.setAttribute('aria-label', 'Menu principal');
            menuTrigger.setAttribute('aria-expanded', 'false');
            menuTrigger.setAttribute('type', 'button');
        }
    }
    
    function createOverlay() {
        if (!menuOverlay) {
            menuOverlay = document.createElement('div');
            menuOverlay.className = 'menu-overlay';
            body.appendChild(menuOverlay);
        }
    }
    
    function bindEvents() {
        // Click hamburger
        if (menuTrigger) {
            menuTrigger.addEventListener('click', toggleMenu);
        }
        
        // Click overlay pour fermer
        if (menuOverlay) {
            menuOverlay.addEventListener('click', closeMenu);
        }
        
        // Liens du menu
        const menuLinks = document.querySelectorAll('.site-menu-main a');
        menuLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                
                // Si c'est un lien interne, faire smooth scroll
                if (href && href.startsWith('#')) {
                    e.preventDefault();
                    closeMenu();
                    
                    setTimeout(() => {
                        const target = document.querySelector(href);
                        if (target) {
                            const headerHeight = header?.offsetHeight || 64;
                            const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;
                            
                            window.scrollTo({
                                top: targetPosition,
                                behavior: 'smooth'
                            });
                        }
                    }, 100);
                } else {
                    // Lien externe, fermer le menu
                    setTimeout(closeMenu, 100);
                }
            });
        });
        
        // Scroll pour effet header
        window.addEventListener('scroll', function() {
            if (!isMobile() || !header) return;
            
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > 20) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
            
            // Fermer menu si scroll important
            if (isMenuOpen && Math.abs(currentScrollY - scrollY) > 100) {
                closeMenu();
            }
        }, { passive: true });
        
        // Fermer avec Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && isMenuOpen) {
                closeMenu();
            }
        });
        
        // Resize
        window.addEventListener('resize', function() {
            if (!isMobile() && isMenuOpen) {
                closeMenu();
            }
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
        if (isMenuOpen) return;
        
        isMenuOpen = true;
        scrollY = window.scrollY;
        
        // Ajouter classes actives
        if (menuTrigger) menuTrigger.classList.add('is-active');
        if (menuBlock) menuBlock.classList.add('is-active');
        if (menuOverlay) menuOverlay.classList.add('is-active');
        
        // Bloquer scroll
        body.style.overflow = 'hidden';
        body.style.position = 'fixed';
        body.style.width = '100%';
        body.style.top = `-${scrollY}px`;
        
        // ARIA
        if (menuTrigger) menuTrigger.setAttribute('aria-expanded', 'true');
        
        // Focus sur premier lien
        setTimeout(() => {
            const firstLink = menuBlock?.querySelector('.site-menu-main a');
            if (firstLink) firstLink.focus();
        }, 300);
    }
    
    function closeMenu() {
        if (!isMenuOpen) return;
        
        isMenuOpen = false;
        
        // Retirer classes actives
        if (menuTrigger) menuTrigger.classList.remove('is-active');
        if (menuBlock) menuBlock.classList.remove('is-active');
        if (menuOverlay) menuOverlay.classList.remove('is-active');
        
        // Restaurer scroll
        body.style.overflow = '';
        body.style.position = '';
        body.style.width = '';
        body.style.top = '';
        
        if (scrollY) {
            window.scrollTo(0, scrollY);
        }
        
        // ARIA
        if (menuTrigger) menuTrigger.setAttribute('aria-expanded', 'false');
    }
    
    // Initialiser quand prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // API publique
    window.mobileMenuSimple = {
        toggle: toggleMenu,
        open: openMenu,
        close: closeMenu,
        isOpen: () => isMenuOpen
    };
    
})();